# Task 02: Black-Scholes-Merton Price and Greeks

**Source:** Master Plan Part E Task 02 | Implements: FR-1, FR-2

## Files
- Create: `src/volsurf/bsm.py`, `tests/test_bsm.py`, `tests/test_greeks_finite_difference.py`, `docs/bsm_derivation.md`

## Interfaces
- `black_scholes(S, K, T, sigma, r, q, option) -> float`
- `delta`, `gamma`, `vega`, `theta`, `rho` — same signature. Theta per year (per-day convention in docstring only).

## Steps
1. **Tests first:**
   - Two textbook benchmark values with citation in test docstring.
   - Put-call parity European: |C − P − (S e^{−qT} − K e^{−rT})| < 1e-10.
   - Monotonicity: call ↓ in K, ↑ in sigma and T (no dividends case).
2. Implement `black_scholes` via `scipy.stats.norm` exact formulas.
3. Edge cases: T = 0 or sigma = 0 → return discounted intrinsic value (no division by zero). Test both.
4. Five analytical Greeks; FD verification: central differences over S ∈ {90,100,110}, moneyness K/S ∈ {0.8,1.0,1.2}, T ∈ {0.02,0.08,0.25,1.0}, σ ∈ {0.1,0.2,0.4}, r = 0.05, q = 0.02. Relative error < 1e-4 (absolute floor 1e-8 near zero).
5. `docs/bsm_derivation.md`: derivation from risk-neutral pricing formula, d1/d2 definitions.

## Exit criteria
Tests green; coverage of `bsm.py` ≥ 95%; ruff clean.

## Gap audit fixes (2026-11-16)
1. **Non-finite inputs:** `_validate` accepts NaN and ±inf (verified: `black_scholes(nan, …)`
   returns NaN). PRD §10 forbids silent NaN. Reject non-finite `S, K, T, sigma, r, q`
   with `ValueError`, and test NaN and inf for each.
2. **Plausible volatility range:** PRD §10 requires volatility validation. Decide and
   document an upper bound (e.g. `sigma <= 5`) or justify leaving it open; test the choice.
3. Remove `test_math_imported` (scaffolding that only exists to keep an import alive).
4. Greek docstrings: state units (per unit of S, per unit of σ, per year, per unit of r).
