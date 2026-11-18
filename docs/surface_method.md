# Volatility surface methodology (Task 09)

## IV table

The cleaned mid for each option is inverted twice (plan-05 B.1):

| column | method |
|---|---|
| `american` | CRR binomial tree, 100 steps, american exercise (inverts `binomial_price`, american=True) |
| `european` | Black-Scholes closed form (comparison only) |

Both use `implied_volatility` with explicit no-arbitrage bounds before solving
and `brentq` over `[sigma_lo, 3.0]`. Reason codes: `ok`, `LOW-NA` (price below
intrinsic), `HIGH-NA` (above upper bound), `NO-BRACKET`, `NO-CONV`. A failing
inversion returns NaN with its reason — never a fabricated IV.

`k = log(K / S)` is the moneyness coordinate.

### Step count

The default American inversion uses **100 tree steps**, not the 500 used in
the Task 05 round-trip tests. Measured on the committed snapshot:

- 100-step price error vs the 500-step reference at SPY-magnitude parameters:
  ≈ 0.04 (≈ 3 cents of IV).
- 100-step American IV differs from the 500-step IV by ≤ 0.0003 absolute on
  the first cleaned rows (mean 0.0002).
- 500 steps would cost ≈ 6 minutes for the 3,575 clean rows; 100 steps runs
  the whole chain in ≈ 1.5 minutes (PRD §10: a surface build under 2 minutes).

The tradeoff is documented here: the surface is a diagnostic of SPY quotes,
and a 3-bp IV error from tree discretization is far below the quote noise the
snapshot already contains (see the arbitrage report).

## Interpolation

`build_surface` fits `scipy.interpolate.LinearNDInterpolator` (a Delaunay
triangulation, C0 — continuous but not smooth) over scattered `(k, T)`
points, then evaluates on a coarse grid `k ∈ [-0.5, 0.5]`, `T ∈ [0.05,
T_max]`. Linear interpolation is the PRD §6.7 minimum; it makes **no
smoothness or no-arbitrage guarantee** — that is why Task 08 screens the raw
quotes and Task 09's calendar check deliberately labels its findings as
model-dependent warnings.

- NaN IV points (solver failures) are dropped before the fit; `method_info`
  logs `dropped_nan` and `n_points`.
- Grid points outside the convex hull of the input cloud are NaN — the
  surface never extrapolates silently.
- Fewer than 4 finite IV points raises `ValueError` (nothing to triangulate).

`method_info` (`results/surface_method.csv`) records the method, input count,
dropped-NaN count, fitted points, and the fitted k-range.

## Term structure and calendar diagnostic

`calendar_diagnostic` compares total variance `IV² * T` at fixed moneyness k
across adjacent maturities, supporting the Task 09 post-IV calendar check.
A decrease in total variance with maturity is flagged:

- **not** proof of executable calendar arbitrage — SPY options are American,
  the quotes are need-not-be-synchronous, and IV is a model inversion;
- reported as a `warning` row so the report can count them without claiming
  a tradable signal (plan-09 edit; PRD §6.6).

## Interpreting the 2026-11-16 snapshot run

`results/iv_table.csv`: 3,575 cleaned options → 3,394 `ok` (94.9%),
181 `LOW-NA`. The `LOW-NA` rows sit below the American intrinsic bound
(consistent with the arbitrage report finding that deep-ITM quotes flagged
American-parity breaches) and are excluded from the fit. American IV spans
≈ 0.067–0.60 across the surface.

`results/iv_surface.csv`: 861 grid points, 367 outside the hull (NaN).
`results/calendar_diagnostic.csv`: 712 warnings across 3,108 comparisons.

Figures under `results/surface/`:

- `smile_<expiry>.png` — 27 smiles (one per cleaned expiry), American IV vs k;
- `term_structure.png` — IV at k = 0 across maturity;
- `surface_3d.png` — triangulated surface over (k, days-to-expiry);
- `iv_american_vs_bs.png` — American vs Black-Scholes IV scatter with y = x,
  the most distinctive diagnostic figure: the gap quantifies the
  early-exercise premium embedded in SPY quotes.

The run is deterministic: a repeat of the CLI produces a byte-identical
`iv_table.csv`.
