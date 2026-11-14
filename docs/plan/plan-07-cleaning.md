# Task 07: Data Cleaning

**Source:** Master Plan Part E Task 07 | Implements: FR-7

## Files
- Create: `src/volsurf/cleaning.py`, `tests/test_cleaning_reconciliation.py`

## Interfaces
- `clean(df, spot, rules) -> (cleaned_df, removal_log)`
- `compute_moneyness(df, spot) -> Series` (K / S)
- `compute_tte(df, snapshot_date) -> Series` (days / 365)

## Rules — applied in this order (master plan Part E, B.6-defined thresholds)
1. Drop bid = 0 or ask = 0.
2. Drop (ask − bid)/mid > 0.5.
3. Compute mid = (bid+ask)/2 as reference price — transformation, not filter; logged as step 3 with zero removals.
4. Drop open interest < 100 or volume < 1.
5. Drop T < 7/365.
6. Drop moneyness outside [0.7, 1.3].

## Steps
1. **Tests first** — synthetic df with one planted row per rule:
   - Each rule removes exactly its planted rows.
   - Reconciliation: raw − Σ(removed) = cleaned, per rule.
   - Mid = arithmetic mean of bid/ask.
   - Band edges: moneyness exactly 0.7 and 1.3 kept; just outside removed.
2. Implement `clean` on a copy; log removed + remaining per rule in order.
3. Thresholds from `config/cleaning.yaml` — never hardcode.
4. Apply to committed snapshot; write `results/cleaning_report.csv`; keep raw chain copy for before/after plots.

## Exit criteria
Reconciliation test green; `cleaning_report.csv` written.
