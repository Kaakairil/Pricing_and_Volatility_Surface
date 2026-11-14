---
description: Task 2 — Black-Scholes-Merton price + Greeks
---

# Task 2: Black-Scholes-Merton (FR-1, FR-2)

## Files
- `src/volsurf/bsm.py`
- `tests/test_bsm.py`, `tests/test_greeks_finite_difference.py`

## Interfaces
- `black_scholes(S, K, T, sigma, r, q, option='call') -> float`
- `delta(S,K,T,sigma,r,q,option)`, same for `gamma/vega/theta/rho`
- Inputs validated: S>0, K>0, T>0, sigma>=0. Raise `ValueError` otherwise.

## Steps
- [ ] Write tests: known textbook call/put values (cite source), put-call parity to 1e-10, price monotonicity in K/sigma/T.
- [ ] Implement `black_scholes` via scipy.stats.norm cdf, exact formulas.
- [ ] Implement 5 analytical Greeks.
- [ ] Write FD test: each Greek vs central finite diff, rel err < 1e-4 over grid (S in {90,100,110}, K moneyness {0.8,1.0,1.2}, T {0.02,0.08,0.25,1}, sigma {0.1,0.2,0.4}, r=0.05, q=0.02).
- [ ] `pytest tests/` green; ruff clean; commit.
