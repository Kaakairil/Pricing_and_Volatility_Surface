---
description: Task 4 — Monte Carlo pricer
---

# Task 4: Monte Carlo (FR-4)

## Files
- `src/volsurf/montecarlo.py`, `tests/test_montecarlo.py`

## Interfaces
- `monte_carlo_price(S, K, T, sigma, r, q, option, paths=200000, seed=0, antithetic=True, control=True) -> (price, standard_error)`

## Steps
- [ ] Write tests: BS price within 3 SE of MC for a few grid points; across ≥10 seeds the estimator variance echoes the reported SE; control variate reduces SE vs raw (assert SE_control < SE_raw).
- [ ] Implement GBM paths: S_T = S exp((r-q-sigma^2/2)T + sigma sqrt(T) Z). Antithetic: pair Z and -Z. Control variate: closed-form BS as control.
- [ ] `pytest tests/` green; ruff; commit.
