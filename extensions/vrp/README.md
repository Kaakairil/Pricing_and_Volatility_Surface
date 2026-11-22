# extensions/vrp — Volatility Risk Premium test

**Question:** does the VIX overstate SPY's subsequent realized volatility?
A positive, statistically significant gap is the volatility risk premium —
the reason short-vol strategies have historically earned a return, and the
honest quantitative basis for any "sell overpriced options" framing.

**Method** (`vrp.py`, network required — yfinance):
- VIX close at window start vs SPY close-to-close realized vol over the
  **next 21 trading days**, annualized, 2018-01-01 → present.
- **Non-overlapping windows** (21-day stride) so consecutive rows share no
  return data — no inflated significance from overlapping samples.
- 95% CI on the mean gap by bootstrap resampling over windows (10,000 draws).
- 2018 and 2020 shown explicitly per the extension brief.

**Findings** (`vrp_summary.txt`, `vrp_windows.csv`):

| period | n | mean gap (vol pts) | 95% CI | % windows positive |
|---|---|---|---|---|
| 2018 | 12 | +0.04 | [−0.044, +0.041] | 67% |
| 2020 | 12 | +2.61 | [−0.099, +0.121] | 75% |
| 2018–now | 106 | **+3.75** | **[+2.03, +5.35]** | **82%** |

The full-period CI excludes zero: the VRP is real. 2018 alone is
indistinguishable from zero; 2020's CI is wide because the March crash
lands inside a handful of windows. `vrp_premium.png` plots the gap; the
visible premium collapses exactly when realized vol spikes (Feb 2018,
Mar 2020, Aug 2024) — short-vol earns steadily and loses violently.

**This is context for the surface's IV levels, not a trading signal.**
It is kept out of `results/` and the main report deliberately: the main
result is the snapshot surface; this is the extension that justifies
interpreting high IV rank as rich pricing.

Run: `.venv/Scripts/python extensions/vrp/vrp.py` then `vrp_plot.py`.
