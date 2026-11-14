---
description: Task 10 — early-exercise premium experiment
---

# Task 10: Early-Exercise Premium (RQ2)

## Files
- `src/volsurf/experiments.py`, `tests/test_experiments.py`

## Interfaces
- `early_exercise_premium(S, K_range, T_range, sigma, r, q) -> DataFrame` — rows: {moneyness, T, american_binom, european_binom, premium}. Fractional premium = premium / european.

## Steps
- [ ] Tests: premium ≥ 0; ≈0 for calls with q=0; premiums rise with r for puts; within grid matches binom Am−Eu.
- [ ] Implement: run binomial pricing (task 3) paired Am/Eu over moneyness {0.9,0.95,1.0,1.05,1.1} × T {1w,1m,3m,1y}, r base + {±1%}: only SPY snapshot params tested here, model experiments not market ones; write `results/early_exercise_premium.csv`.
- [ ] Verify no NaN in outputs; commit.
