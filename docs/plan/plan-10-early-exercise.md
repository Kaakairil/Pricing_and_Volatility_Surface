# Task 10: Early-Exercise Premium Experiment

**Source:** Master Plan Part E Task 10 (Review B.6) | Implements: RQ2

## Files
- Create: `src/volsurf/experiments.py`, `tests/test_experiments.py`

## Interfaces
- `early_exercise_premium(S, moneyness, T_grid, sigma, r, q, steps=1000) -> DataFrame` — columns: moneyness, T, option, american, european, premium, premium_pct

## Grid (aligned to PRD §9.1)
- Moneyness {0.8, 0.9, 1.0, 1.1, 1.2}
- T ∈ {1 week, 1 month, 3 months, 1 year}
- Rate: base ± 100 bp. Dividend: SPY recorded value. Sigma: SPY ATM implied vol from snapshot.

## Note
SPY calls have a **nonzero** early-exercise premium because q > 0 (dividends). This is a model experiment using SPY parameters — separate from market analysis.

## Steps
1. **Tests first:**
   - premium ≥ −1e-10 for all rows.
   - q = 0 → call premium < 1e-6.
   - With SPY dividend yield, call premium positive for at least one configuration (deep ITM near ex-dividend-like); document why.
   - Put premium increases with r across sensitivity. Output has no NaN.
2. Implement grid as paired American and European binomial prices.
3. Write `results/early_exercise_premium.csv` and `results/rate_sensitivity.csv`.
4. Verify no NaN.

## Exit criteria
Tests green; CSVs written.
