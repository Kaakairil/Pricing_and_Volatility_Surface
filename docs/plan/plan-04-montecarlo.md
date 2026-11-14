# Task 04: Monte Carlo Pricer

**Source:** Master Plan Part E Task 04 | Implements: FR-4

## Files
- Create: `src/volsurf/montecarlo.py`, `tests/test_montecarlo.py`

## Interfaces
- `monte_carlo_price(S, K, T, sigma, r, q, option, paths=200_000, seed=0, antithetic=True, control=True) -> (price, standard_error)`

## Steps
1. **Tests first:**
   - Black-Scholes price within 3 SE of MC at four grid points.
   - Over 10 seeds, spread of estimates consistent with reported SE (ratio 0.7–1.3).
   - Control variate reduces SE vs raw estimator (assert SE_control < SE_raw).
2. **Implement GBM terminal:** S_T = S exp((r − q − σ²/2) T + σ √T Z), Z ~ N(0,1).
3. **Antithetic:** pair Z and −Z; SE over pair averages (pairs = independent units).
4. **Control variate (master plan B.4):** X = e^{−rT} S_T with E[X] = S e^{−qT}; Y = e^{−rT} payoff; β = Cov(Y,X)/Var(X) on same paths; adjusted estimator Ȳ − β(X̄ − S e^{−qT}). Document control choice in docstring.
5. Return SE of final estimator.

## Exit criteria
Tests green.
