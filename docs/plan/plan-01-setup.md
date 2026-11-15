# Task 01: Repository Setup

**Source:** VolSurf Master Plan Part E Task 01 | Implements: PRD §10, §11

## Decisions in force (from master plan Part B)
- Underlying SPY; American-style pricing (binomial) with Black-Scholes for comparison only.
- Rate: constant 3-month T-bill (FRED DTB3) at snapshot date → continuous compounding.
- Single snapshot, committed to repo; SVI stretch first; moneyness grid {0.8,0.9,1.0,1.1,1.2}.

## Conventions (from master plan Part D)
- T in years (days/365); volatility/rates decimals; rates continuously compounded.
- Moneyness K/S; log-moneyness k = ln(K/S). Option types `"call"`/`"put"` strings, validated by one helper.
- Failures never return NaN silently — reason code or `ValueError`. Every stochastic function takes explicit `seed`.
- Mid = (bid+ask)/2 only reference price. Type hints, docstrings with units, ruff clean, no prints in library.
- Work on `main` only — no feature branches.

## Files
- Create: `pyproject.toml`, `Makefile`, `config/market.yaml`, `config/cleaning.yaml`, `config/pricing_grid.yaml`, `.gitignore`, `src/volsurf/__init__.py`

## Steps
1. `pyproject.toml` — Python ≥3.11, setuptools, pinned deps: numpy, scipy, pandas, yfinance, matplotlib, pyyaml, pytest, pytest-cov, ruff, requests. `[tool.pytest.ini_options]` markers `network`/`slow`; `[tool.coverage.report] fail_under = 85`.
2. `Makefile` targets: `setup`, `test`, `lint`, `fetch` (manual, live, network), `all` (committed snapshot only, no network), `figures`, `report`, `clean`.
3. `config/market.yaml`: `ticker: SPY`, `snapshot_date` (filled Task 06), `rate_series: DTB3`, `rate_tenor_days: 91`, `rate_value` (Task 06), `dividend_method: trailing_12m`, `dividend_yield` (Task 06), `rate_sensitivity_bp: [-100, 100]`.
4. `config/cleaning.yaml`: spread ≤ 50% mid; open interest ≥ 100; volume ≥ 1; T ≥ 7d; moneyness 0.7–1.3.
5. `config/pricing_grid.yaml`: PRD §9.1 grid (moneyness {0.8,0.9,1.0,1.1,1.2}, T {1w,1m,3m,1y}, σ {0.1,0.2,0.4}).
6. `.gitignore`: `data/raw/`, `__pycache__/`, `.venv*`, `.ruff_cache/`, `.pytest_cache/`, `results/figures/`, `.claude/settings.local.json`. Do NOT ignore `data/snapshots/` or `results/*.csv`.
7. `src/volsurf/__init__.py` with `__version__`.

## Exit criteria
- `pip install -e .` succeeds; `python -c "import volsurf"` works; `ruff check .` passes; `pytest` runs clean (zero tests).

## Gap audit fixes (2026-11-16) — found reviewing tasks 01–04
1. **Config types:** `config/pricing_grid.yaml` maturities must parse as floats, not the
   strings `'1.0/52'`, `'1.0/12'`. Use decimal literals (`0.0192307692`, `0.0833333333`)
   or `maturity_days: [7, 30, 91, 365]`. Add a test that loads the YAML and asserts
   `isinstance(maturity, float)` for every entry.
2. **Generated artifacts:** `.gitignore` must include `.coverage`, `.coverage.*`,
   `htmlcov/`; `git rm --cached .coverage` — the file is currently tracked.
3. **Make unavailable:** `make` is not installed on the development machine (Windows).
   Keep `Makefile`, but record the direct equivalents (`.venv/Scripts/python -m pytest
   -m "not network"`, `.venv/Scripts/ruff check src tests`) in the README, and fix the
   `clean` target so it actually runs (current `python -c` one-liner is invalid).
4. **Coverage gate:** `fail_under = 85` is configured but nothing runs coverage. Add
   `--cov=volsurf --cov-report=term-missing` to the test target so the gate is enforced.
