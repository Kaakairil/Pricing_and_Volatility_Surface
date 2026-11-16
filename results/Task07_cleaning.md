# Task 07 — Data Cleaning (PRD §6.5)

**Snapshot:** `data/snapshots/spy_2026-11-16.csv` (SPY, 2026-11-16, spot 754.37)

## What this task delivers

- `src/volsurf/cleaning.py` — `clean(df, spot, rules, snapshot_date)` implementing
  the six PRD §6.5 pipeline steps in order, plus `compute_moneyness` and `compute_tte`.
- `tests/test_cleaning_reconciliation.py` — 9 tests, all green (see below).
- `results/cleaning_report.csv` — per-step removal log for the real snapshot.

## Pipeline result (real snapshot)

Raw chain: **10,354** option rows (32 expiries, calls + puts).

| # | Rule (PRD §6.5) | Removed | Remaining | Notes |
|---|---|---|---|---|
| 1 | zero / non-finite bid or ask | 1,272 | 9,082 | no usable quote |
| 2 | (ask−bid)/mid > 50% | 749 | 8,333 | wide/spread synthetic |
| 3 | mid = (bid+ask)/2 | 0 | 8,333 | additive column, no removal |
| 4 | OI < 100 or volume < 1 | 3,545 | 4,788 | liquidity floor |
| 5 | T < 7 days | 512 | 4,276 | expiry-day noise |
| 6 | moneyness outside [0.7, 1.3] | 701 | 3,575 | surface fitting band |

**Cleaned count: 3,575** contracts, with derived columns `mid`, `tte` (years,
365-day basis), `moneyness` added. Reconciliation: 10,354 − 6,779 = 3,575 ✓

## Tests (RED → GREEN)

`tests/test_cleaning_reconciliation.py` — 9 tests:

- Each rule removes exactly its planted rows; removal log reconciles
  (raw − Σ removed = cleaned).
- Mid = arithmetic mean of bid/ask.
- Band edges (moneyness exactly 0.7 and 1.3) kept; just outside (0.6999) removed.
- Zero bid, zero ask, both-zero all dropped by rule 1.
- Thresholds come from the injected `rules` dict (tighter OI floor test), never
  hardcoded.
- Input never mutated.
- Empty input → empty cleaned, zero removals, 6-step log.

All **9 passed**.

## Files

| Path | Purpose |
|---|---|
| `src/volsurf/cleaning.py` | implementation |
| `src/volsurf/config_io.py` | reads thresholds from `config/cleaning.yaml` |
| `src/volsurf/cli.py` | `python -m volsurf.cli clean` — reproduces this report |
| `tests/test_cleaning_reconciliation.py` | 9 tests |
| `tests/test_config_io.py` | config loader tests (partial/missing config) |
| `tests/test_cli.py` | CLI dispatcher + clean round-trip on a snapshot |
| `results/cleaning_report.csv` | real-snapshot removal log |
| `results/Task07_cleaning.md` | this report |

## Thresholds (config-driven, Option A)

Thresholds are **not** hardcoded in `cleaning.py`. With `rules=None`,
`clean()` loads them from `config/cleaning.yaml` through
`volsurf.config_io.get_cleaning_rules()`. Tests inject dicts directly to prove
thresholds are injected; `tests/test_config_io.py` proves the YAML file is the
production source (partial config falls back per-key, missing file falls back
to defaults). The CLI command reproduces this report from the committed
snapshot:

```
python -m volsurf.cli clean data/snapshots/spy_2026-11-16.csv -o results
```

Verified output: `cleaned 10354 -> 3575 rows (spot 754.37, date 2026-11-16)`
with the same six-step removal log as the table above.
