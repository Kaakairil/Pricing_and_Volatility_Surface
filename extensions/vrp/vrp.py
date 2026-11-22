"""Volatility risk premium (VRP) test (extension, Task 12 follow-up).

Does the VIX overstate SPY's subsequent realized volatility? For each
window start date t, compare VIX close at t with SPY's realized vol over
the NEXT 21 trading days. Positive gaps mean options were priced above
what later happened — the premium a short-vol position earns.

Output: one row per non-overlapping window (21-trading-day stride), so
windows share no data. Two block-bootstrap CIs on the mean gap; 2018 and
2020 shown explicitly.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "extensions" / "vrp"
WINDOW = 21  # trading days (~1 month)


def realized_vol_next(prices: pd.Series, start: int, window: int = WINDOW) -> float:
    """Annualized close-to-close vol over the window AFTER index `start`."""
    seg = prices.iloc[start + 1 : start + 1 + window]
    if len(seg) < window:
        return float("nan")
    rets = np.log(seg / seg.shift(1)).dropna()
    return float(rets.std(ddof=1) * np.sqrt(252))


def build_windows(spy: pd.Series, vix: pd.Series) -> pd.DataFrame:
    """Non-overlapping 21-day windows on common dates."""
    # yfinance indexes are tz-aware; normalize both to plain dates so the
    # reindex below aligns on the calendar day, not the offset.
    spy = spy.copy()
    vix = vix.copy()
    spy.index = pd.to_datetime(spy.index.date)
    vix.index = pd.to_datetime(vix.index.date)
    vix = vix.reindex(spy.index).dropna()
    spy = spy.reindex(vix.index)
    rows = []
    start = 0
    while start + WINDOW < len(vix):
        rows.append(
            {
                "date": vix.index[start].date(),
                "vix": float(vix.iloc[start]),
                "rv_next": realized_vol_next(spy, start),
            }
        )
        start += WINDOW
    df = pd.DataFrame(rows)
    # VIX is quoted in vol points (9.77 = 9.77%); realized vol is a decimal.
    df["gap"] = df["vix"] / 100.0 - df["rv_next"]
    return df.dropna(subset=["rv_next"])


def bootstrap_ci(gaps: np.ndarray, n_boot: int = 10_000, seed: int = 0) -> tuple[float, float]:
    """95% CI on the mean gap by iid block bootstrap over windows."""
    rng = np.random.default_rng(seed)
    means = rng.choice(gaps, size=(n_boot, len(gaps)), replace=True).mean(axis=1)
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    spy = yf.Ticker("SPY").history(start="2018-01-01", interval="1d")["Close"]
    vix = yf.Ticker("^VIX").history(start="2018-01-01", interval="1d")["Close"]
    windows = build_windows(spy, vix)
    windows.to_csv(OUT / "vrp_windows.csv", index=False)

    gaps = windows["gap"].to_numpy()
    lo, hi = bootstrap_ci(gaps)
    pct = 100 * (gaps > 0).mean()

    for year in (2018, 2020):
        sub = windows[windows["date"].astype(str).str.startswith(str(year))]
        if len(sub):
            ylo, yhi = bootstrap_ci(sub["gap"].to_numpy())
            print(
                f"{year}: n={len(sub)} mean gap={sub['gap'].mean():.4f} "
                f"95% CI [{ylo:.4f}, {yhi:.4f}] pct_pos={100 * (sub['gap'] > 0).mean():.0f}%"
            )
    print(
        f"ALL 2018-now: n={len(gaps)} mean gap={gaps.mean():.4f} "
        f"95% CI [{lo:.4f}, {hi:.4f}] pct_pos={pct:.0f}%"
    )
    (OUT / "vrp_summary.txt").write_text(
        f"VRP (VIX - next-21d realized vol), non-overlapping windows\n"
        f"n={len(gaps)} windows\n"
        f"mean gap={gaps.mean():.4f} vol points\n"
        f"95% block-bootstrap CI [{lo:.4f}, {hi:.4f}]\n"
        f"positive in {pct:.0f}% of windows\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
