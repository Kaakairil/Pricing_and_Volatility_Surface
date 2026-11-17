"""Offline tests for the fetch orchestrator (Task 06, plan-06 gap item 4).

``fetch.main`` is the network step; here every network boundary is faked
(requests, yfinance, fetch_chain) so the orchestration itself — FRED
percent→decimal conversion, snapshot write, metadata, config fill — is
verified without touching the network.  The ``network`` marker is unused
here: these tests must run in the default ``make test`` suite so the
coverage gate measures them.
"""

import math

import pandas as pd
import pytest
import yaml

from volsurf import fetch
from volsurf.market_data import load_snapshot
from volsurf.rates import risk_free_from_dtb3


class _FakeResponse:
    def __init__(self, text):
        self.text = text

    def raise_for_status(self):
        pass


class TestLatestDtb3:
    def test_picks_latest_nonempty_observation(self, monkeypatch):
        # FRED CSVs are chronological (oldest first); the newest row may be
        # empty (holiday/weekend lag) and must be skipped, not read as 0.
        text = "DATE,DTB3\n2026-11-10,4.20\n2026-11-12,4.14\n2026-11-13,\n"
        monkeypatch.setattr(fetch.requests, "get", lambda *a, **k: _FakeResponse(text))
        value, date = fetch._latest_dtb3()
        assert value == 4.14
        assert date == "2026-11-12"

    def test_raises_when_all_values_empty(self, monkeypatch):
        text = "DATE,DTB3\n2026-11-13,\n2026-11-12,\n"
        monkeypatch.setattr(fetch.requests, "get", lambda *a, **k: _FakeResponse(text))
        with pytest.raises(RuntimeError, match="DTB3"):
            fetch._latest_dtb3()


class TestTrailingDividend:
    def test_returns_float_from_info(self, monkeypatch):
        class FakeTicker:
            def __init__(self, ticker):
                self.info = {"trailingAnnualDividendRate": 7.53}

        monkeypatch.setattr(fetch.yf, "Ticker", FakeTicker)
        assert fetch._trailing_dividend("SPY") == pytest.approx(7.53)

    def test_raises_when_info_lacks_rate(self, monkeypatch):
        class FakeTicker:
            def __init__(self, ticker):
                self.info = {}

        monkeypatch.setattr(fetch.yf, "Ticker", FakeTicker)
        with pytest.raises(RuntimeError, match="trailingAnnualDividendRate"):
            fetch._trailing_dividend("SPY")


class TestFetchChainColumnNames:
    def test_raw_yf_iv_renamed(self, monkeypatch):
        # plan-06 item 1: Yahoo's black-scholes-implied column is kept but
        # renamed so nobody mistakes it for our own inversion output.
        import volsurf.market_data as md

        class FakeChain:
            def __init__(self):
                self.calls = pd.DataFrame(
                    {"strike": [100.0], "bid": [8.0], "ask": [8.4], "impliedVolatility": [0.2]}
                )
                self.puts = pd.DataFrame(
                    {"strike": [100.0], "bid": [6.0], "ask": [6.4], "impliedVolatility": [0.25]}
                )

        class FakeTicker:
            def __init__(self, ticker):
                self.info = {"regularMarketPrice": 754.37}
                self.options = ["2026-12-18"]

            def option_chain(self, expiry):
                return FakeChain()

        monkeypatch.setattr(md.yf, "Ticker", FakeTicker)
        df, spot, _ = md.fetch_chain("SPY")
        assert "yf_iv" in df.columns
        assert "impliedVolatility" not in df.columns
        assert spot == pytest.approx(754.37)


class TestMain:
    @pytest.fixture()
    def fetched(self, monkeypatch, tmp_path):
        snap_dir = tmp_path / "snapshots"
        config_path = tmp_path / "market.yaml"
        config_path.write_text(
            "ticker: SPY\nsnapshot_date: '2000-01-01'\nrate_value: 0.0\ndividend_yield: 0.0\n",
            encoding="utf-8",
        )
        chain_df = pd.DataFrame(
            {
                "strike": [100.0, 100.0],
                "expiry": ["2027-03-19", "2027-03-19"],
                "option": ["call", "put"],
                "bid": [8.0, 6.0],
                "ask": [8.4, 6.4],
                "volume": [10, 10],
                "openInterest": [100, 100],
            }
        )
        monkeypatch.setattr(fetch, "_latest_dtb3", lambda: (4.14, "2026-11-12"))
        monkeypatch.setattr(
            fetch, "fetch_chain", lambda t: (chain_df, 754.37, "2026-11-16T21:00:05+00:00")
        )
        monkeypatch.setattr(fetch, "_trailing_dividend", lambda t: 7.53)
        monkeypatch.setattr(fetch, "SNAPSHOT_DIR", snap_dir)
        monkeypatch.setattr(fetch, "CONFIG", config_path)
        fetch.main()
        return snap_dir, config_path

    def test_snapshot_written_with_metadata(self, fetched):
        snap_dir, _ = fetched
        df, meta = load_snapshot(snap_dir / "spy_2026-11-16.csv")
        assert len(df) == 2
        assert meta["spot"] == pytest.approx(754.37)
        assert meta["snapshot_date"] == "2026-11-16"
        assert meta["row_counts"] == {"total": 2, "calls": 1, "puts": 1, "expiries": 1}
        assert meta["rate_source"] == "FRED DTB3 2026-11-12"
        # plan-06 item 5: provenance of the spot quote (yfinance exposes no
        # quote timestamp, so we record at least where the number came from).
        assert "spot_source" in meta

    def test_fred_percent_converted_to_decimal(self, fetched):
        # THE bug class: FRED quotes DTB3 in percent (4.14); main must divide
        # by 100 *before* the bank-discount conversion.
        snap_dir, _ = fetched
        _, meta = load_snapshot(snap_dir / "spy_2026-11-16.csv")
        expected_r = risk_free_from_dtb3(0.0414, tenor_days=91)
        assert meta["rate_value"] == pytest.approx(expected_r)
        assert meta["rate_value"] == pytest.approx(0.0417, abs=1e-3)

    def test_dividend_yield_is_continuous_conversion(self, fetched):
        snap_dir, _ = fetched
        _, meta = load_snapshot(snap_dir / "spy_2026-11-16.csv")
        assert meta["dividend_yield"] == pytest.approx(math.log(1 + 7.53 / 754.37))
        assert meta["dividend_method"] == "trailing_12m"

    def test_config_updated(self, fetched):
        _, config_path = fetched
        cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        expected_r = risk_free_from_dtb3(0.0414, tenor_days=91)
        assert cfg["snapshot_date"] == "2026-11-16"
        assert cfg["fetch_time_utc"] == "2026-11-16T21:00:05+00:00"
        assert cfg["rate_value"] == pytest.approx(expected_r)
        assert cfg["dividend_yield"] == pytest.approx(math.log(1 + 7.53 / 754.37))
