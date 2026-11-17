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

## Gap audit updates (2026-11-16)
1. **YAML types:** quote-free `1.0/52` and `1.0/12` parse as strings, not arithmetic. Store numeric maturities as decimals (`0.0192307692`, `0.0833333333`) and test parsed types/values.
2. **Generated coverage data:** add `.coverage`, `.coverage.*`, and `htmlcov/` to `.gitignore`; untrack `.coverage`. It is currently tracked despite being generated.
3. **Enforce coverage:** `fail_under = 85` alone does not collect coverage. Configure the test command with `--cov=volsurf --cov-report=term-missing`.
4. **Clean target:** replace current invalid `python -c` loop and shell-specific cleanup with a tested, working command. `make` is not installed in this Windows environment; document equivalent direct commands in README, but do not treat missing local `make` as a package defect.
5. **Reproducibility:** dependency ranges (`>=…,<…`) are not locked versions. Pin exact versions or add a committed lock/constraints file, then verify clean editable installation from that contract.

## Gap audit round 2 (2026-11-18) — status of the 2026-11-16 items
1. YAML types — **done**: `pricing_grid.yaml` stores decimals; `tests/test_config.py` checks types/values.
2. Generated coverage data — **done**: `.coverage*`/`htmlcov/` ignored, nothing tracked.
3. Coverage enforcement — **done**: offline fetch tests (plan-06) added; gate now passes at 95.4% (≥ 85). Verified: `make test` equivalent passes.
4. Clean target — **done**: one-liner runs successfully on Windows; equivalent documented in README.
5. Dependency lock — **done**: committed `constraints.txt` (exact direct-dependency versions from the working venv), wired into `make setup` and README.

## Additional findings (2026-11-18)
6. **`make all` / `figures` / `report` reference nonexistent scripts** (`scripts/run_pipeline.py`, `scripts/make_figures.py`, `scripts/make_report.py`). Expected — those are Tasks 08-12 deliverables; do not "fix" by deleting the targets. Note kept here so a fresh-clone `make all` failure is not mistaken for a defect.
