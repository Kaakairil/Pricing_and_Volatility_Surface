---
description: Task 11 — SVI fit (stretch)
---

# Task 11: SVI Slice Fit (FR-10, stretch)

## Files
- `src/volsurf/svi.py`, `tests/test_svi.py`

## Interfaces
- `fit_svi_slice(strikes, tte, ivs, x0=None) -> params` — params {a,b,m,rho,sigma}; raw fit per expiry slice.
- `check_butterfly_arbitrage(params) -> bool` — SVI no-arbitrage condition (Gatheral bound: g(x)+v(x)^2 conditions).
- `total_variance_slice(params, x) -> array` — for checks/plots.

## Steps
- [ ] Tests: on synthetic Gaussian smile, fit recovers params within tol; butterfly arb correctly detected on an engineered violating slice; fit slice passes arb check on clean synthetic data.
- [ ] Implement: SVI raw parameterization v(x)=a+b(rho(x−m)+sqrt((x−m)²+σ²)); fit via `scipy.optimize.least_squares`; butterfly condition per Gatheral 2014.
- [ ] Run on 2–3 cleaned expiries; report SVI vs interpolated surface in `results/`; add figure.
- Doc note → `docs/svi_method.md`. Commit.
