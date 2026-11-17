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

## Gap audit updates (2026-11-16)
1. **Antithetic standard error:** compute standard error over independent pair-level observations, not individual paths. When using control variate, form pair means for both discounted payoff `Y` and control `X`, estimate beta from those paired observations, then calculate SE from adjusted pair estimates. Existing implementation uses individual observations; across 50 seeds observed dispersion / reported SE was 1.44, while pair-level SE gave 1.05. Treat these as diagnostics, not universal constants.
2. **Seed-spread regression:** strengthen beyond 10 seeds; verify empirical standard deviation against the mean reported SE with a tolerance justified by sampling variability (e.g. 30+ fixed seeds, 0.8–1.25).
3. **Degenerate control:** at `T == 0` or `sigma == 0`, control variance is zero and current code returns `(nan, nan)` with a warning. Skip control adjustment when variance is zero; estimator should return deterministic price and SE 0.
4. **Sample count contract:** require at least two observations for a defined sample SE; when antithetic is enabled, either require even `paths >= 2` or define `paths` as pair count and adjust API/docs consistently. Do not silently discard odd paths.
5. Reject non-finite inputs as specified for BSM validation; test this public entry point too.
6. Add European binomial-vs-Monte-Carlo agreement test required by PRD §8. Use discounted-stock control `X=e^{-rT}S_T` with known mean `S e^{-qT}` as the valid control variate; clarify this choice against PRD's ambiguous phrase “closed-form price as the control.”

## Gap audit round 2 (2026-11-18) — status of the 2026-11-16 items
1. Antithetic SE over pair means — **done**: pair means are the independent units for Y and X; β from paired observations.
2. Seed-spread regression — **done**: 30 fixed seeds, ratio bounds 0.8–1.25.
3. Degenerate control — **done**: zero-variance control skipped, returns (price, 0.0); tested at T = 0.
4. Sample count contract — **done**: `paths >= 2` required; antithetic requires even count (explicit error, no silent discard).
5. Non-finite input rejection — **done** (delegates to `_validate`; NaN spot test).
6. Binomial-vs-MC agreement — **done** (`TestBinomialCrossCheck`).

All six 2026-11-16 items closed; no round-2 work for this task.
