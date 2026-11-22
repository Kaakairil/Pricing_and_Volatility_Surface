# SPY Volatility Surface — Results Report

**Snapshot:** SPY 2026-11-16, spot 754.37,
10,354 raw quotes (5,440 calls /
4,914 puts), 32 expiries.
**Rate:** FRED DTB3 2026-11-12 = 0.0422.
**Dividend yield:** 0.0075 (trailing_12m).

## Research questions

### RQ1 — Do the three pricers agree?

Cross-method agreement at PRD §9.1 grid points (from the test suite, all green):

| Comparison | Tolerance | Result |
|---|---|---|
| Black-Scholes vs European binomial (500 steps) | abs error < 0.01 | pass |
| Black-Scholes vs Monte Carlo | within 3 standard errors | pass (30 seeds, spread/SE ratio 1.12) |
| Binomial American convergence (1000 vs 10000 steps) | abs error < 0.005 | pass |
| Put-call parity (model prices) | machine precision | pass |
| Greeks vs central finite difference | rel error < 1e-4 | pass |
| IV round-trip (recover σ from price) | abs error < 1e-6 | pass |

Run `.venv/Scripts/python -m pytest -m "not network"` to reproduce.

### RQ2 — What is the American early-exercise premium worth?

Paired American vs European CRR binomial prices (1000 steps, σ = 0.2,
r = 0.04219617863034214, q = 0.007477573830616421 — documented SPY parameters). The premium is the value of
early exercise.

| Moneyness (K/S) | 1-year put premium ($) | premium % |
|---|---|---|
| 0.80 | 0.2028 | 3.32% |
| 0.90 | 0.8701 | 4.38% |
| 1.00 | 2.6937 | 5.77% |
| 1.10 | 6.5525 | 7.47% |
| 1.20 | 13.5033 | 9.60% |

Key observations:
- **Calls at SPY's dividend yield (q = 0.007477573830616421) are never worth exercising
  early** — the premium is floating-point zero on the whole grid. Early
  exercise is a put phenomenon (or a high-q phenomenon).
- **Puts**: premium grows with moneyness (deep ITM) and with maturity.
  Max on this grid: 13.5033 (9.60% of
  the European value) at K/S = 1.2, T = 1.0y.
- **Rate sensitivity** (ATM, T = 0.25, r ± 100 bp around 0.04219617863034214): put premium
  rises with r (0.3583 → 0.7244),
  call premium is flat (q > 0 keeps calls alive). Matches PRD §9.2.

### RQ3 — What does the SPY volatility surface look like?

From `results/iv_table.csv`: **3,394 of 3,575 cleaned quotes
(95%) invert to a finite American IV.**

**American vs Black-Scholes IV** (the headline): inverting the same mid
with the American CRR tree (100 steps) and with the European BS formula
gives two IV estimates that differ by
**mean 0.00229 vol points, median 0.00047,
p95 0.01070** across all 3,394 quotes. The
difference is the early-exercise premium expressed in vol terms: puts away
from ATM show the largest gaps. Figure:
`results/surface/iv_american_vs_bs.png`.

**Smile and skew:** at the longest expiry (2.18y), measured in a
symmetric |k| ≤ 0.08 window (matched moneyness on both sides of ATM),
the left-wing IV exceeds the right-wing IV by **+0.0166 vol points**
(0.1989 vs 0.1823, n = 6/9).
A raw mean-left minus mean-right over *all* strikes gives
+0.0331, but that compares 5 deep-put quotes against 19
shallow-call quotes and is not a like-for-like measure. Equity-index skew
is present but shallower than PRD §9.3's illustrative ≈ +0.08 on this
single snapshot. Figures: `results/surface/smile_*.png`.

**Term structure:** ATM IV rises with maturity on this snapshot —
short-dated options price less total variance. The leftmost points of the
curve can be missing: near the short-T edge the C0 interpolator has no
grid points inside its convex hull and correctly refuses to extrapolate.
Figure: `results/surface/term_structure.png`.

**Surface:** C0 `LinearNDInterpolator` over (log-moneyness, maturity),
861 grid points. Calendar diagnostic: total
variance decreases on **712 of 3,108 adjacent tte-pairs
(22.9%)**. The rate, not the raw count, is the honest
measure: adjacent-strike sampling noise inflates it, and PRD §6.6 frames
these as model-dependent (American IV is not guaranteed calendar-monotone
under discrete exercise) rather than as data errors. SVI fits 3 slices
with RMSE-in-IV
0.0038–0.0078, all
butterfly-clean (`results/svi_fit.csv`). Figures:
`results/surface/surface_3d.png`, `results/surface/svi_vs_interpolated.png`.

### RQ4 — How many arbitrage violations does cleaning remove?

Raw snapshot: **4,061 midpoint violations** across
16,793 tests; after the PRD §6.5 cleaning rules
(6,779 quote removals, `results/cleaning_report.csv`):
**1,083 midpoint violations** — a
**73% reduction.**

Spread-robust violations (robust to wide markets):
**2,227 → 441** after cleaning. Residuals are honest:
the remaining violations are concentrated in
american_parity and call_convexity at the far wings where quotes are
stale even after filtering (`results/arbitrage_report.csv`).

Flag counts by check:

| check | raw midpoint flags | cleaned midpoint flags |
|---|---|---|
| american_parity | 1,938 | 546 |
| call_monotonicity | 296 | 4 |
| put_monotonicity | 194 | 30 |
| call_convexity | 1,633 | 503 |

## Limitations

1. **Free, possibly delayed data.** yfinance quotes are 15-min-delayed
   snapshots; mids from wide markets are noisy even after cleaning.
2. **Single snapshot.** One day (2026-11-16) — no claims about how the
   surface moves over time.
3. **Continuous dividend approximation.** A trailing-12m continuous yield
   q = 0.007477573830616421 approximates discrete quarterly dividends; short-dated puts
   are the most affected.
4. **C0 linear interpolation.** The surface is piecewise-linear in
   (log-moneyness, T); it is not differentiable, so smooth-model tools
   (SABR greeks, exact Dupire) do not apply. SVI is fitted on 3 slices
   only as a cross-check.
5. **No Heston / stochastic vol.** Explicitly out of scope (PRD §16.4).
6. **Rate sensitivity is parameterized, not fitted.** The ±100 bp grid
   perturbs r; it does not fit a curve.
7. **American IV uses a 100-step tree.** Trunk precision ~1e-3 in price,
   which propagates to IV as a small positive bias on long-dated puts.


## Reproduce

```bash
make setup && make all && make test
```

Every number in this report is computed from a committed CSV in
`results/` by `scripts/make_report.py` (or from the test suite); no
number is hardcoded.
