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

## Gap audit fixes (2026-11-16)
1. **SE must use pair averages (step 3 was not implemented).** With antithetic variates the
   estimator's SE is over the `n` pair means, not the `2n` individual paths. Verified defect:
   50-seed dispersion / reported SE = 1.44 (correct pair-average SE gives 1.05). Fix the
   estimator and strengthen `test_estimates_consistent_with_reported_se` to 30 seeds with
   ratio tolerance 0.8–1.25.
2. **Degenerate control variate:** `np.var(x)` is 0 when `T == 0` or `sigma == 0`, giving a
   divide-by-zero warning and `(nan, nan)` (verified). Skip the control variate in that case
   (or raise a documented error), and test `T=0`, `sigma=0`.
3. **Path count contract:** odd `paths` silently truncates (`paths=5` → 4 draws). Either
   require `paths >= 2` and an even count when `antithetic=True`, or document that `paths`
   is the number of simulated paths (pairs = paths // 2). Test the contract.
4. **Binomial vs Monte Carlo cross-check (PRD §8):** add agreement test within combined
   tolerance.
5. Reject non-finite inputs (consistent with the BSM validation fix).
