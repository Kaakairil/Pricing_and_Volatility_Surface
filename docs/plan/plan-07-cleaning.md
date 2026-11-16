# Task 07: Data Cleaning

**Source:** Master Plan Part E Task 07 | Implements: FR-7

## Files
- Create: `src/volsurf/cleaning.py`, `tests/test_cleaning_reconciliation.py`
- Config plumbing (Option A): `src/volsurf/config_io.py`, `src/volsurf/cli.py`,
  `tests/test_config_io.py`, `tests/test_cli.py`

## Interfaces
- `clean(df, spot, rules=None, snapshot_date=None, log_path=None) -> (cleaned_df, removal_log)`
  — when `rules=None`, thresholds load from `config/cleaning.yaml` via
  `volsurf.config_io.get_cleaning_rules()`; tests inject dicts to prove nothing is hardcoded.
- `compute_moneyness(df, spot) -> Series` (K / S)
- `compute_tte(df, snapshot_date) -> Series` (days / 365)
- `config_io.get_cleaning_rules(config_dir=None) -> dict` — reads `config/cleaning.yaml`,
  validates the six keys, falls back to defaults for missing/non-numeric entries.
- CLI: `python -m volsurf.cli clean <snapshot.csv> [-o results]` — checksum-verified load
  via `market_data.load_snapshot`, spot + snapshot date from snapshot metadata.

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
3. Thresholds from `config/cleaning.yaml` — never hardcode. `cleaning.py` never
   opens the file itself; `config_io.get_cleaning_rules` is the single reader
   (tested against partial/missing configs).
4. Apply to committed snapshot via the CLI (`python -m volsurf.cli clean`);
   write `results/cleaning_report.csv` and `results/cleaned_<date>.csv`.
   The earlier `extract`/`subset`/`snapshots`/`chain` CLI scaffolding referenced
   modules that never existed (`volsurf.cli_utils`, `volsurf.extract.cli_run`,
   `volsurf.merge`, `volsurf.vol_engine`); it is removed rather than stubbed —
   arbitrage/surface commands attach in Tasks 08-12.

## Exit criteria
Reconciliation test green; `cleaning_report.csv` written; CLI reproduces the
same counts from the committed snapshot; thresholds provably come from the YAML.

## Result (2026-11-16 snapshot, spot 754.37)

Raw chain: **10,354** rows (32 expiries, calls + puts).

| # | Rule | Removed | Remaining |
|---|---|---|---|
| 1 | zero/non-finite bid or ask | 1,272 | 9,082 |
| 2 | spread > 50% of mid | 749 | 8,333 |
| 3 | mid = (bid+ask)/2 | 0 | 8,333 |
| 4 | OI < 100 or volume < 1 | 3,545 | 4,788 |
| 5 | T < 7 days | 512 | 4,276 |
| 6 | moneyness outside [0.7, 1.3] | 701 | 3,575 |

Cleaned: **3,575** rows with derived `mid`, `tte`, `moneyness`. Reconciliation:
10,354 − 6,779 = 3,575 ✓. Reproduce with
`python -m volsurf.cli clean data/snapshots/spy_2026-11-16.csv -o results`.
Artifacts: `results/cleaning_report.csv`, `results/cleaned_2026-11-16.csv`.
28 tests across cleaning/config-io/CLI green.
