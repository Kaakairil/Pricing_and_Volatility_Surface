"""Data-cleaning reconciliation tests (Task 07, PRD §6.5).

One planted row per rule in a synthetic chain; each rule removes exactly
its own rows, and the counts reconcile: raw - sum(removed) = cleaned.
Thresholds come from ``config/cleaning.yaml``, never hardcoded.
"""

import pandas as pd
import pytest

from volsurf.cleaning import clean, compute_moneyness, compute_tte

SNAPSHOT_DATE = "2026-11-16"
FAR_EXPIRY = "2027-03-19"  # 123 days after snapshot date


def _rules():
    return {
        "max_spread_pct_of_mid": 0.50,
        "min_open_interest": 100,
        "min_volume": 1,
        "min_t_days": 7,
        "moneyness_min": 0.7,
        "moneyness_max": 1.3,
    }


def _row(**overrides):
    """One valid chain row (passes every rule), with overrides applied."""
    row = {
        "strike": 100.0,
        "expiry": FAR_EXPIRY,
        "bid": 8.0,
        "ask": 8.4,
        "openInterest": 1000,
        "volume": 10,
    }
    row.update(overrides)
    return row


def _chain(*rows):
    return pd.DataFrame(list(rows))


class TestComputeHelpers:
    def test_moneyness_strike_over_spot(self):
        df = pd.DataFrame({"strike": [70.0, 100.0, 130.0]})
        out = compute_moneyness(df, 100.0)
        assert list(out) == pytest.approx([0.7, 1.0, 1.3])

    def test_tte_days_over_365(self):
        df = pd.DataFrame({"expiry": [SNAPSHOT_DATE, FAR_EXPIRY]})
        tte = compute_tte(df, SNAPSHOT_DATE)
        # 2026-11-16 -> 2027-03-19 is 123 days
        assert tte.iloc[0] == 0.0
        assert tte.iloc[1] == pytest.approx(123 / 365)


class TestCleanReconciliation:
    def test_each_rule_removes_only_its_planted_rows(self):
        planted = _chain(
            _row(bid=0.0),  # rule 1: zero bid
            _row(bid=8.0, ask=16.0),  # rule 2: spread (16-8)/12 = 0.67 > 0.5
            _row(openInterest=50),  # rule 4: OI < 100
            _row(volume=0),  # rule 4: volume < 1
            _row(expiry="2026-11-17"),  # rule 5: T = 1 day < 7
            _row(strike=50.0),  # rule 6: moneyness 0.5 < 0.7
        )
        df = pd.concat([_chain(_row()), planted], ignore_index=True)
        cleaned, log = clean(df, spot=100.0, rules=_rules(), snapshot_date=SNAPSHOT_DATE)

        assert len(cleaned) == 1
        # PRD §6.5: six steps; step 3 is the mid transformation (0 removals).
        assert log["removed"].tolist() == [1, 1, 0, 2, 1, 1]
        # Reconciliation: raw - sum(removed) = cleaned
        assert len(df) - log["removed"].sum() == len(cleaned)

    def test_mid_is_arithmetic_mean(self):
        cleaned, _ = clean(
            _chain(_row(bid=8.0, ask=8.6)), spot=100.0, rules=_rules(), snapshot_date=SNAPSHOT_DATE
        )
        assert cleaned["mid"].iloc[0] == pytest.approx(8.3)

    def test_band_edges_kept_just_outside_removed(self):
        df = _chain(_row(strike=70.0), _row(strike=130.0), _row(strike=69.99))
        cleaned, _ = clean(df, spot=100.0, rules=_rules(), snapshot_date=SNAPSHOT_DATE)
        assert sorted(cleaned["strike"].tolist()) == [70.0, 130.0]

    def test_zero_bid_and_zero_ask_both_dropped(self):
        df = _chain(_row(bid=0.0), _row(ask=0.0), _row(bid=0.0, ask=0.0), _row())
        cleaned, log = clean(df, spot=100.0, rules=_rules(), snapshot_date=SNAPSHOT_DATE)
        assert len(cleaned) == 1
        assert log["removed"].iloc[0] == 3

    def test_never_mutates_input(self):
        df = _chain(_row())
        original = df.copy(deep=True)
        clean(df, spot=100.0, rules=_rules(), snapshot_date=SNAPSHOT_DATE)
        pd.testing.assert_frame_equal(df, original)

    def test_empty_input(self):
        cleaned, log = clean(
            pd.DataFrame(columns=["strike", "expiry", "bid", "ask", "openInterest", "volume"]),
            spot=100.0,
            rules=_rules(),
            snapshot_date=SNAPSHOT_DATE,
        )
        assert len(cleaned) == 0
        assert len(log) == 6
        assert log["removed"].sum() == 0

    def test_thresholds_come_from_rules_not_hardcode(self):
        # Tighter OI floor removes a row the default would keep.
        tight = _rules() | {"min_open_interest": 2000}
        cleaned, log = clean(
            _chain(_row(openInterest=1500)), spot=100.0, rules=tight, snapshot_date=SNAPSHOT_DATE
        )
        assert len(cleaned) == 0
        assert log["removed"].iloc[3] == 1


class TestSpotValidation:
    @pytest.mark.parametrize("bad", [float("nan"), float("inf"), 0.0, -100.0])
    def test_rejects_nonpositive_or_nonfinite_spot(self, bad):
        df = _chain(_row())
        with pytest.raises(ValueError, match="spot"):
            clean(df, spot=bad, rules=_rules(), snapshot_date=SNAPSHOT_DATE)
