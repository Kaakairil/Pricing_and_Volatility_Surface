# Task 11: SVI Slice Fit (stretch)

**Source:** Master Plan Part E Task 11 | Implements: FR-10 (stretch). Start after Task 10 + report draft.

## Files
- Create: `src/volsurf/svi.py`, `tests/test_svi.py`, `docs/svi_method.md`

## Interfaces
- `fit_svi_slice(k, total_var, weights=None, x0=None) -> params` — params = {a, b, rho, m, sigma}
- `svi_total_variance(params, k) -> array`
- `check_butterfly(params, k_grid) -> (bool, min_g)`

## Model (master plan B.4)
- Total variance: w(k) = a + b(ρ(k−m) + √((k−m)² + σ²)).
- **Constraints enforced during fit** (not just checked after): b ≥ 0, |ρ| < 1, σ > 0, a + b σ √(1−ρ²) ≥ 0.
- **Butterfly density (Gatheral 2014):** g(k) = (1 − k w′/(2w))² − (w′)²/4 · (1/w + 1/4) + w″/2 ≥ 0 for all k on dense grid.

## Steps
1. **Tests first:**
   - Synthetic smile with known params: fit recovers within 1e-3.
   - Constraint violations rejected by fit.
   - Engineered violating slice flagged by `check_butterfly`; fitted clean slice passes.
2. Fit on total variance w = IV²·T (not IV), `scipy.optimize.least_squares` with bounds for constraints.
3. Fit 2–3 cleaned expiries, ≥ 5 strikes each; write `results/svi_fit.csv` (params, fit RMSE, butterfly result).
4. Add SVI-vs-interpolated figure.

## Exit criteria
Tests green; fits + figure produced. If time runs out: skip, state out of scope in report.
