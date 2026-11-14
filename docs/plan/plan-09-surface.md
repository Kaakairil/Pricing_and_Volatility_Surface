# Task 09: Volatility Surface and Plots

**Source:** Master Plan Part E Task 09 | Implements: FR-9

## Files
- Create: `src/volsurf/surface.py`, `src/volsurf/plots.py`, `tests/test_surface.py`, `docs/surface_method.md`

## Interfaces
- `compute_iv_table(df, spot, r, q, style="american") -> DataFrame` — IV (American) + IV (Black-Scholes) per option, with reason codes
- `build_surface(iv_table) -> (grid_df, method_info)` — scattered-data interpolation over (k, T)
- `plot_smiles`, `plot_term_structure`, `plot_surface_3d`, `plot_error_heatmap`, `plot_pre_post_cleaning`, `plot_iv_american_vs_bs`

## Steps
1. **Tests first:**
   - Interpolated surface reproduces input IVs at node points within 1e-8.
   - NaN IV points (solver failure) dropped before fitting; count logged.
   - Insufficient data (< 5 strikes in a slice) raises clear error or skips with log entry.
   - Out-of-hull grid points are NaN — never extrapolate silently.
2. Implement: k = ln(K/S); `scipy.interpolate.LinearNDInterpolator` on (k, T). Document that linear is C0 — no smoothness/no-arbitrage guarantee (addressed by Task 08 surface check).
3. Term structure: IV at fixed k across expiries, interpolated from surface.
4. Generate all figures from cleaned snapshot. Include American-vs-Black-Scholes IV comparison — most distinctive figure.
5. `docs/surface_method.md`.

## Exit criteria
Tests green; all figures generated.
