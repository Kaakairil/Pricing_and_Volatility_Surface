# Task 09: Volatility Surface and Plots

**Source:** Master Plan Part E Task 09 | Implements: FR-9

## Status: DONE (2026-11-19)

Implemented via TDD (tests first, `tests/test_ivtable.py`):
- `src/volsurf/surface.py` — `compute_iv_table`, `build_surface`,
  `calendar_diagnostic`.
- `src/volsurf/plots.py` — smile / term structure / 3D / American-vs-BS
  figures (error-heatmap + pre-post-cleaning left to tasks 10/12).
- `src/volsurf/cli.py` — `surface` subcommand.
- `src/volsurf/implied_vol.py` — clamped `_american_sigma_floor` to at least
  `SIGMA_LO` (r == q no longer passes sigma_lo = 0 to the tree; the gap-audit
  ValueError on `d < e^{(r-q)dt} < u` is fixed).
- Docs: `docs/surface_method.md`, this file.

Run on committed snapshot (spot 754.37): 3,575 cleaned → 3,394 `ok` /
181 `LOW-NA`. 100-step American inversion chosen (≤ 3 bp IV error vs
500-step, whole chain ≈ 1.5 min — meets PRD §10's 2-min surface target;
rationale in `docs/surface_method.md`). 27 smiles + term structure + 3D +
American-vs-BS figures under `results/surface/`. Calendar diagnostic:
712 warnings / 3,108 comparisons (model-dependent, not executable).
Deterministic repeat verified (byte-identical `iv_table.csv`).

## Gap audit round 3 (2026-11-20) — findings in this task's own code

1. **`plot_term_structure` reads the grid, not IVs — CLOSED (2026-11-23).**
   The report now carries the sentence: near the short-T edge the C0
   interpolator has no grid points inside its convex hull and correctly
   refuses to extrapolate (report/report.md RQ3).
2. **RQ3 skew — CLOSED (2026-11-23).** report.md RQ3 now computes the skew
   from `results/iv_table.csv` in a symmetric |k| ≤ 0.08 window at the
   longest expiry: **+0.0166 vol points** (0.1989 left vs 0.1823 right).
   The earlier ≈ +0.08 estimate came from unmatched means (5 deep puts vs
   19 shallow calls = +0.0331) — not like-for-like; the report states both
   and why the matched window is the honest measure.
3. **Calendar warnings — CLOSED (2026-11-23).** Report RQ3 now presents
   the rate: 712 of 3,108 adjacent tte-pairs (22.9%), with the §6.6
   model-dependent framing and the adjacent-strike-noise caveat.

## Original brief (kept for reference)



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
3. Term structure: IV at fixed k across expiries, interpolated from surface. Own the post-IV calendar diagnostic: compare total variance on comparable supported points; label decreases in American IV total variance as model-dependent warnings, not executable arbitrage.
4. Generate all figures from cleaned snapshot. Include American-vs-Black-Scholes IV comparison — most distinctive figure.
5. `docs/surface_method.md`.

## Exit criteria
Tests green; all figures generated.
