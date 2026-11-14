---
description: Task 7 — data cleaning rules
---

# Task 7: Data Cleaning (FR-7)

## Files
- `src/volsurf/cleaning.py`, `tests/test_cleaning_reconciliation.py`

## Interfaces
- `clean(df, rules: dict) -> (cleaned_df, removal_log)` — `removal_log`: per-rule {rule_id: {removed, remaining}}.
- Rules applied in PRD §6.5 order: 1 zero bid/ask, 2 spread > 50% of mid, 3 use mid as ref price, 4 OI/vol below threshold, 5 T < 7d, 6 moneyness outside 0.7–1.3.
- `compute_moneyness(df, spot) -> Series` — strike/spot.

## Steps
- [ ] Tests (synthetic df): each rule removes exactly its rows; reconciliation holds (`raw - sum(removed) == cleaned`); mid price computed correctly; moneyness band edges respected.
- [ ] Implement `clean` in order, mutating a copy, logging each removal count; thresholds from `config/cleaning.yaml`.
- [ ] Apply to real snapshot, write `results/cleaning_report.csv`. Commit.
