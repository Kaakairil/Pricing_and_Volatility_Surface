"""CLI coverage (Task 07/08): dispatcher + clean subcommand against a snapshot.

Regression guard: the earlier CLI imported phantom modules (cli_utils,
extract.cli_run, merge, vol_engine) and dispatched on a string. These tests
exercise the real handler path against a checksum-verified snapshot.
"""

import pandas as pd
import pytest

from volsurf.cli import main
from volsurf.market_data import save_snapshot

EXPIRY = "2027-03-19"


def _chain():
    return pd.DataFrame(
        [
            {
                "strike": 100.0,
                "expiry": EXPIRY,
                "bid": 8.0,
                "ask": 8.4,
                "openInterest": 1000,
                "volume": 10,
            },
            {
                "strike": 100.0,
                "expiry": EXPIRY,
                "bid": 0.0,
                "ask": 8.4,
                "openInterest": 1000,
                "volume": 10,
            },
            {
                "strike": 50.0,
                "expiry": EXPIRY,
                "bid": 8.0,
                "ask": 8.4,
                "openInterest": 1000,
                "volume": 10,
            },
        ]
    )


def _snapshot(tmp_path):
    df = _chain()
    meta = {"ticker": "SPY", "snapshot_date": "2026-11-16", "spot": 100.0}
    return save_snapshot(df, meta, tmp_path)


def test_main_clean_roundtrip(tmp_path):
    csv = _snapshot(tmp_path)
    out = tmp_path / "out"

    rc = main(["clean", str(csv), "-o", str(out)])

    assert rc == 0
    assert (out / "cleaning_report.csv").exists()
    cleaned = pd.read_csv(out / "cleaned_2026-11-16.csv")
    # 3 rows: zero-bid removed by rule 1, moneyness 0.5 removed by rule 6.
    assert len(cleaned) == 1
    assert cleaned["mid"].iloc[0] == pytest.approx(8.2)
    assert "tte" in cleaned.columns and "moneyness" in cleaned.columns


def test_main_missing_snapshot_fails(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        main(["clean", str(tmp_path / "nope.csv"), "-o", str(tmp_path / "out")])
    assert exc.value.code == 2


def test_unknown_command_errors(capsys):
    with pytest.raises(SystemExit):
        main(["extract"])  # removed phantom subcommand
