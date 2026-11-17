# Pricing_and_Volatility_Surface

VolSurf — SPY options pricing library + volatility-surface report.

## Quick start

```bash
.venv/Scripts/python -m pip install -e ".[dev]" -c constraints.txt
```

`constraints.txt` pins the exact direct-dependency versions the library was
developed and tested against (see plan-01); drop the `-c constraints.txt` to
float within the `pyproject.toml` ranges.

### Direct commands (Windows, no `make` required)

```bash
# tests, offline only
.venv/Scripts/python -m pytest -m "not network"

# tests with coverage gate (fail_under = 85)
.venv/Scripts/python -m pytest -m "not network" --cov=volsurf --cov-report=term-missing

# lint + format check
.venv/Scripts/ruff check src tests
.venv/Scripts/ruff format --check src tests
```

### Makefile targets (optional — needs GNU make)

| target  | purpose                                              |
| ------- | ---------------------------------------------------- |
| setup   | create venv + install package editable               |
| test    | run offline tests with coverage gate                 |
| lint    | ruff check + format check                            |
| fetch   | MANUAL live snapshot fetch (network, market hours)   |
| all     | full pipeline from committed snapshot (offline)      |
| figures | regenerate figures only                              |
| report  | regenerate report only                               |
| clean   | remove caches + generated results                    |

`make` is not required: every target maps to a direct `.venv/Scripts/python ...` command above.

## Repository layout

```
src/volsurf/        pricing + analytics
tests/              pytest suite (markers: network, slow)
docs/plan/          per-task plan briefs (01..12)
config/             pricing grid + market conventions
data/raw/           snapshot inputs (gitignored)
results/            CSVs committed, figures gitignored
```

Snapshots and result CSVs are committed; raw data and figures are not. See `docs/plan/plan-01-setup.md` for the full rationale.
