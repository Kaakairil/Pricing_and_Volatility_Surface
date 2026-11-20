# SVI slice fit methodology (Task 11, stretch)

## Model

Raw SVI total variance (Gatheral 2004), fitted per expiry:

    w(k) = a + b * (rho * (k - m) + sqrt((k - m)^2 + sigma^2))

with `k = log(K/S)`. Fitting is done on **total variance** `w = IV^2 * T`
(not IV), as the parameterization is designed for.

## Fit procedure

- `scipy.optimize.least_squares` (residuals in total variance) with **hard
  bounds** enforcing `b >= 0`, `|rho| < 1`, `sigma > 0` during the fit;
- the remaining admissibility condition `a + b*sigma*sqrt(1 - rho^2) >= 0`
  is checked after each start's optimum; violating optima are discarded;
- four deterministic multi-starts scan for the global optimum
  (`fit_svi_slice(k, w, x0=...)` bypasses the scan with a user start);
- slices with < 5 points, non-finite inputs, or non-positive w raise
  `ValueError` — the fit never returns a fabricated parameter set.

## Butterfly check

Gatheral (2014) density condition on a dense grid (1001 points, k-range
extended by 0.2 on each side):

    g(k) = (1 - k w'/(2w))^2 - (w')^2/4 * (1/w + 1/4) + w''/2 >= 0

`check_butterfly` returns `(ok, min_g)`. All three fitted snapshot slices
pass (min_g 0.32 / 0.32 / 0.47).

## Slice selection and identification caveat

From the committed 2026-11-16 snapshot (3,394 ok rows), the 3 widest
expiries are fitted: tte = 1.08 / 1.18 / 2.08 years, 142–158 strikes each,
k ∈ [-0.353, 0.262].

**Caveat (important for reading `results/svi_fit.csv`):** the k-range is
one-sided (84% of strikes are OTM puts). On one-sided data the raw SVI
parameters are **poorly identified**: two of three slices converge to the
|rho| = 0.99 bound with very large b (≈ 21–23) and compensating m — a flat
"ridge" of (b, rho, m, sigma) combinations that produce nearly the same
curve over the observed k-range. Consequences:

- the **fitted curve** is reliable (RMSE in IV 0.004–0.008, butterfly-clean);
- the **individual parameters are not** — do not interpret `b`, `rho`, `m`
  across slices without extra regularization (e.g. the quasi-explicit
  Zeliade or calendar-constrained fits), which is out of scope here.

## Fit quality (2026-11-16 snapshot)

| tte (y) | n | RMSE in IV | butterfly min_g |
|--------:|---:|-----------:|----------------:|
| 1.0849  | 158 | 0.0078 | 0.321 |
| 1.1808  | 147 | 0.0038 | 0.320 |
| 2.0822  | 142 | 0.0059 | 0.465 |

## Outputs

- `results/svi_fit.csv` — params + RMSE + butterfly result per slice;
- `results/surface/svi_vs_interpolated.png` — SVI curve vs the Task 09
  `LinearNDInterpolator` cross-section per fitted slice, with the cleaned
  ok-IV scatter. The SVI curve is smooth by construction; the interpolator
  is piecewise-linear between quotes — their difference visualizes how much
  shape the parametric assumption adds.
