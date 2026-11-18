"""Offline American quote diagnostics and report integration (Task 08)."""

import pandas as pd
import pytest

from volsurf.binomial import binomial_price
from volsurf.cli import main
from volsurf.market_data import save_snapshot

DATE = "2026-11-16"
EXPIRY = "2027-03-19"


def quote(strike, bid, ask=None, option="call", expiry=EXPIRY):
    return {
        "strike": strike,
        "bid": bid,
        "ask": bid if ask is None else ask,
        "option": option,
        "expiry": expiry,
        "openInterest": 1000,
        "volume": 10,
    }


def checks(rows, **overrides):
    from volsurf.arbitrage import run_checks

    args = {"spot": 100.0, "r": 0.0, "q": 0.0, "snapshot_date": DATE, **overrides}
    return run_checks(pd.DataFrame(rows), **args).set_index(["expiry", "check"])


def counts(report, check, expiry=EXPIRY):
    return tuple(report.loc[(expiry, check), ["tested", "midpoint_flags", "spread_robust_flags"]])


@pytest.mark.parametrize("ask, robust", [(12, 0), (10, 1)])
def test_parity_quote_interval_touch_is_not_robust(ask, robust):
    report = checks([quote(100, 10, ask), quote(100, 12, option="put")])
    assert counts(report, "american_parity") == (1, 1, robust)
    assert report.loc[(EXPIRY, "american_parity"), "sample_strikes"] == "100"


def test_american_crr_prices_fit_bounds_not_european_equality():
    T, r, q = 123 / 365, 0.05, 0.02
    rows = [
        quote(K, binomial_price(100, K, T, 0.25, r, q, side, steps=500), option=side)
        for K in (80, 100, 120)
        for side in ("call", "put")
    ]
    report = checks(rows, r=r, q=q)
    assert counts(report, "american_parity") == (3, 0, 0)


@pytest.mark.parametrize("side, prices", [("call", [8, 9, 12]), ("put", [12, 10, 8])])
def test_strike_flags_for_both_sides(side, prices):
    rows = [
        quote(K, mid - 0.5, mid + 0.5, side) for K, mid in zip((95, 100, 110), prices, strict=True)
    ]
    assert counts(checks(rows), f"{side}_monotonicity") == (2, 2, 1 if side == "call" else 2)


@pytest.mark.parametrize(
    "middle, ask, expected", [(7, 7, (1, 0, 0)), (7, 9, (1, 1, 0)), (8, 8, (1, 1, 1))]
)
def test_convexity_uses_strike_distances_and_quote_endpoints(middle, ask, expected):
    assert (
        counts(checks([quote(95, 9), quote(100, middle, ask), quote(110, 3)]), "call_convexity")
        == expected
    )


def test_exclusions_and_expiry_isolation():
    later = "2027-06-18"
    report = checks(
        [
            quote(90, 8),
            quote(90, 0),  # Ambiguous even if one quote is invalid.
            quote(95, 10, 9),
            quote(100, float("inf")),
            quote(105, 5),
            quote(110, 4, option="straddle"),
            quote(115, 3, expiry=DATE),
            quote(105, 5, option="put", expiry=later),
            quote(110, 2, expiry=later),
        ]
    )
    row = report.loc[(EXPIRY, "call_monotonicity")]
    assert (row.input_quotes, row.eligible_quotes, row.tested) == (6, 1, 0)
    assert counts(report, "american_parity", later) == (0, 0, 0)
    assert report.loc[(DATE, "american_parity"), "eligible_quotes"] == 0


@pytest.mark.parametrize(
    "override",
    [{"spot": 0}, {"r": -0.01}, {"q": float("nan")}, {"tol": -1}, {"snapshot_date": "bad"}],
)
def test_invalid_market_inputs_raise(override):
    with pytest.raises(ValueError):
        checks([quote(100, 5)], **override)


def test_cli_reports_both_stages_deterministically(tmp_path):
    rows = [quote(100, 8), quote(100, 8, option="put"), quote(105, 0), quote(110, 10)]
    meta = {"snapshot_date": DATE, "spot": 100.0, "rate_value": 0.04, "dividend_yield": 0.01}
    snapshot = save_snapshot(pd.DataFrame(rows), meta, tmp_path)
    output = tmp_path / "out"
    args = ["arbitrage", str(snapshot), "-o", str(output)]
    assert main(args) == 0
    report = output / "arbitrage_report.csv"
    data = pd.read_csv(report)
    vertical = data[data.check == "call_monotonicity"].set_index("stage")
    assert set(vertical.index) == {"raw", "cleaned"}
    assert vertical.input_quotes.to_dict() == {"raw": 4, "cleaned": 3}
    assert vertical.spread_robust_flags.to_dict() == {"raw": 1, "cleaned": 1}
    first = report.read_bytes()
    assert main(args) == 0
    assert report.read_bytes() == first


def test_cli_requires_snapshot_rate(tmp_path, capsys):
    snapshot = save_snapshot(pd.DataFrame([quote(100, 5)]), {"snapshot_date": DATE}, tmp_path)
    with pytest.raises(SystemExit) as exc:
        main(["arbitrage", str(snapshot), "-o", str(tmp_path / "out")])
    assert exc.value.code == 2
    assert "rate_value" in capsys.readouterr().err
    assert not (tmp_path / "out").exists()
