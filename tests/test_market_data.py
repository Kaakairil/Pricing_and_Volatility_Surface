"""Market-data snapshot and rate/dividend conversion tests (Task 06).

Unit tests are offline: ``fetch_chain`` is marked ``network`` and skipped by
default.  Snapshot save/load round-trips and the checksum guard are tested
against a small synthetic chain.
"""

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from volsurf.market_data import (
    fetch_chain,
    load_snapshot,
    save_snapshot,
)
from volsurf.rates import dividend_yield_continuous, risk_free_from_dtb3


@pytest.fixture()
def chain():
    """Small deterministic synthetic chain: 2 calls + 1 put at one expiry."""
    df = pd.DataFrame(
        {
            "strike": [100.0, 110.0, 100.0],
            "expiry": ["2026-12-31", "2026-12-31", "2026-12-31"],
            "option": ["call", "call", "put"],
            "bid": [8.0, 3.0, 6.0],
            "ask": [8.4, 3.2, 6.2],
            "lastPrice": [8.2, 3.1, 6.1],
            "volume": [500, 300, 400],
            "openInterest": [2000, 1500, 1800],
        }
    )
    return df


class TestSaveLoadRoundTrip:
    def test_roundtrips_dataframe_exactly(self, chain, tmp_path):
        meta = {"ticker": "SPY", "snapshot_date": "2026-12-31"}
        path = save_snapshot(chain, meta, tmp_path)
        loaded_df, loaded_meta = load_snapshot(path)
        assert_frame_equal(loaded_df, chain)
        assert loaded_meta == meta

    def test_metadata_fields_present(self, chain, tmp_path):
        meta = {
            "ticker": "SPY",
            "snapshot_date": "2026-12-31",
            "fetch_time_utc": "2026-12-31T12:00:00+00:00",
            "spot": 754.37,
            "rate_value": 0.0414,
            "rate_source": "FRED DTB3 2026-11-12",
            "dividend_yield": 0.0137,
            "dividend_method": "trailing_12m",
            "row_counts": {"total": 3, "calls": 2, "puts": 1},
        }
        path = save_snapshot(chain, meta, tmp_path)
        metadata_file = path.with_suffix(".metadata.json")
        with open(metadata_file, encoding="utf-8") as f:
            stored = json.load(f)
        for key, _ in meta.items():
            assert key in stored

    def test_raises_on_any_checksum_mismatch(self, chain, tmp_path):
        path = save_snapshot(chain, {"ticker": "SPY"}, tmp_path)
        # Framing metadata is outside the checksummed CSV; corrupt the CSV bytes.
        csv_file = path
        data = bytearray(csv_file.read_bytes())
        data[3] ^= 0xFF
        csv_file.write_bytes(data)
        with pytest.raises(ValueError, match="checksum"):
            load_snapshot(path)

    @pytest.mark.parametrize(
        "fetch_time, snapshot_date",
        [
            ("2026-11-16T21:00:05+00:00", "2026-11-16"),  # matching -> ok
            ("2026-11-16T21:00:05+00:00", "2026-11-17"),  # mismatch -> error
        ],
    )
    def test_snapshot_date_must_match_fetch_time(self, chain, tmp_path, fetch_time, snapshot_date):
        # plan-06 item 3: a fetch that crosses UTC midnight would be filed
        # under the wrong date; fail loudly instead of mislabeling.
        meta = {"ticker": "SPY", "snapshot_date": snapshot_date, "fetch_time_utc": fetch_time}
        if snapshot_date == fetch_time[:10]:
            path = save_snapshot(chain, meta, tmp_path)
            assert path.exists()
        else:
            with pytest.raises(ValueError, match="snapshot_date"):
                save_snapshot(chain, meta, tmp_path)


class TestCommittedSnapshotReload:
    def test_committed_snapshot_loads_and_reconciles(self):
        # plan-06 item 2: the committed snapshot must stay loadable offline
        # (checksum + metadata) — guards accidental schema/metadata drift.
        path = Path(__file__).resolve().parents[1] / "data" / "snapshots" / "spy_2026-11-16.csv"
        if not path.exists():
            pytest.skip("committed snapshot not present in this checkout")
        df, meta = load_snapshot(path)
        assert len(df) == meta["row_counts"]["total"]
        assert (df["option"] == "call").sum() == meta["row_counts"]["calls"]
        assert (df["option"] == "put").sum() == meta["row_counts"]["puts"]
        assert df["expiry"].nunique() == meta["row_counts"]["expiries"]
        assert meta["spot"] > 0
        assert meta["fetch_time_utc"][:10] == meta["snapshot_date"]


class TestRates:
    def test_risk_free_from_dtb3_hand_value(self):
        # P = 1 - 0.05*91/360; r = -ln(P)*365/91
        expected = -math.log(1 - 0.05 * 91 / 360) * 365 / 91
        assert risk_free_from_dtb3(0.05, tenor_days=91) == pytest.approx(expected)

    def test_risk_free_zero_discount(self):
        assert risk_free_from_dtb3(0.0, tenor_days=91) == pytest.approx(0.0)

    def test_dividend_yield_continuous_hand_value(self):
        # discrete yield = 1.0/20.0 = 5%; q = ln(1.05)
        expected = math.log(1.05)
        assert dividend_yield_continuous(1.0, 20.0) == pytest.approx(expected)

    def test_dividend_zero(self):
        assert dividend_yield_continuous(0.0, 100.0) == pytest.approx(0.0)

    def test_dividend_value_per_unit_spot(self):
        # y = trailing_amount/spot, q = ln(1+y)
        y = 3.0 / 100.0
        assert dividend_yield_continuous(3.0, 100.0) == pytest.approx(math.log(1 + y))


class TestDividendMethod:
    def test_attribute_documented(self):
        import volsurf.rates as rates

        assert hasattr(rates, "dividend_yield_continuous")
        doc = rates.dividend_yield_continuous.__doc__ or ""
        assert "trailing" in doc


@pytest.mark.network
class TestFetchChain:
    def test_fetches_spy_chain(self):
        df, spot, fetch_time = fetch_chain("SPY")
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert "strike" in df.columns
        assert np.isfinite(spot)
        assert fetch_time is not None
