---
description: Task 9 — volatility surface + plots
---

# Task 9: Volatility Surface (FR-9)

## Files
- `src/volsurf/surface.py`, `src/volsurf/plots.py`, `tests/test_surface.py`

## Interfaces
- `build_surface(df) -> (grid_df, method)` — IV from `implied_volatility` on clean mids, then interpolate over (log-moneyness, T). Grid returned for plotting.
- `plot_smiles`, `plot_term_structure`, `plot_surface_3d`, `plot_error_heatmap`, `plot_pre_post_cleaning` — save PNGs to `results/figures/`.

## Steps
- [ ] Tests: interpolation reproduces input IVs at node points within tol; empty/insufficient slices handled; deep-ITM NaN IVs (from solver failure) dropped from fit.
- [ ] Implement: moneyness = log(K/spot); per-expiry slice; `scipy.interpolate` (documented choice: linear on (log-moneyness, T) grid as default); term structure at fixed log-moneyness via slice cross-section.
- [ ] Generate all figures from cleaned snapshot. Commit.
- Method note → `docs/surface_method.md`.
