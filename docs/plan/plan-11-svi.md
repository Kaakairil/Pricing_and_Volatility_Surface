# Task 11: SVI Slice Fit (stretch)

**Source:** Master Plan Part E Task 11 | Implements: FR-10 (stretch). Start after Task 10 + report draft.

## Status: DONE (2026-11-20)

TDD (tests first, `tests/test_svi.py` — 11 tests, RED watched first):
- `src/volsurf/svi.py` — `svi_total_variance`, `fit_svi_slice` (hard bounds +
  4 deterministic multi-starts + admissibility filter), `check_butterfly`
  (Gatheral 2014 g(k) ≥ 0), `fit_snapshot_slices`, `write_svi_fit_csv`,
  `plot_svi_vs_interpolated`.
- `docs/svi_method.md` — model, fit procedure, **identification caveat**
  (one-sided k-data ⇒ raw (b, rho, m, sigma) poorly identified: two slices
  hit the |rho| = 0.99 bound with b ≈ 21–23; the fitted *curve* is reliable,
  the individual parameters are not).
- Snapshot run: 3 widest expiries (tte 1.08/1.18/2.08y, 142–158 strikes),
  RMSE in IV 0.004–0.008, all butterfly-clean (min_g ≥ 0.32).
  Outputs: `results/svi_fit.csv`, `results/surface/svi_vs_interpolated.png`.

Pre-implementation notes (plan edit first per AGENTS.md):
- **Fit total variance `w = IV²·T`** (not IV), `scipy.optimize.least_squares`
  with hard bounds: b ≥ 0, |ρ| < 1, σ > 0, and the a + bσ√(1−ρ²) ≥ 0
  convexity-side constraint enforced via parameterization rather than
  post-hoc rejection only.
- **Raw-parameter fit with bounds** (a, b, ρ, m, σ) + many-start x0 scan;
  `check_butterfly` (Gatheral 2014 g(k) ≥ 0) runs on a dense grid per slice
  and is reported per slice in `results/svi_fit.csv` alongside fit RMSE.
- **Slice selection from the committed snapshot:** 27 expiries have ≥ 8
  ok-rows; the fit picks the 3 widest (k-range ≈ 0.61 wide, 124–158 strikes
  each: tte ≈ 0.84 / 1.08 / 1.18y). Note the k-range is one-sided (kmin
  −0.353, kmax 0.262) — the fit sees mostly OTM puts, standard for SPY.
- **Figure:** SVI fit vs the Task 09 `LinearNDInterpolator` cross-section at
  each fitted expiry, into the results figures dir.

## Files
- Create: `src/volsurf/svi.py`, `tests/test_svi.py`, `docs/svi_method.md`
- Figure: `plot_svi_vs_interpolated` (in svi.py, Agg backend)

## Interfaces
- `fit_svi_slice(k, total_var, weights=None, x0=None) -> params` — params = {a, b, rho, m, sigma}
- `svi_total_variance(params, k) -> array`
- `check_butterfly(params, k_grid) -> (bool, min_g)`
- `plot_svi_vs_interpolated(iv_table, fits, out_dir)` — SVI curve vs Task-09 interpolator per slice

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
