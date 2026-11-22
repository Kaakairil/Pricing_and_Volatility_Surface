# Task 12: Report, README, Reproducibility

**Source:** Master Plan Part E Task 12 (Review B.6) | Implements: G7

## Files
- Create: `README.md` (finalize), `Makefile` (final), `report/report.md`, `report/summary.md`, `tests/test_reproducibility.py`

## Steps
1. **Finalize Makefile:**
   - `all`: committed snapshot only → clean → arbitrage → surface → experiments → figures → report. No network.
   - `fetch`: manual, live, network. Not part of `all`.
   - `test`: `pytest -m "not network"` with coverage.
   - `lint`: `ruff check . && ruff format --check .`
2. **Coverage (fixed command):** `pytest --cov=volsurf --cov-report=term-missing`; ≥ 85% on `bsm`, `binomial`, `montecarlo`, `implied_vol`; record per-module numbers.
3. `tests/test_reproducibility.py`: run pipeline twice on committed snapshot → byte-identical CSVs. Fix nondeterminism (seeds, ordering, float formatting).
4. **README.md:** what project is/is not, quickstart, `make all` < 10 min on committed snapshot, environment, structure tree, data provenance, links to report + docs.
5. **report/report.md** (6–10 pp), one section per RQ:
   - RQ1 pricer agreement tables + verification grid; RQ2 premium figure/table; RQ3 smile, term structure, 3D surface, American-vs-BS IV comparison; RQ4 arbitrage before/after cleaning with honest residuals.
   - Limitations: free data, single snapshot, continuous dividend approximation, linear interpolation (C0), no Heston, rate sensitivity.
6. **report/summary.md:** one page, non-specialist.
7. **Clean-clone test:** clone into empty dir → `make setup && make all && make test`; record output + env in `results/run_metadata.json`.

## Exit criteria
Clean-clone run passes; coverage target met; report + summary written; tagged `v1.0` (Heston explicitly out of scope per PRD §16.4).

## Gap audit round 3 (2026-11-20) — inputs waiting for this task

Found in the plans 1–11 re-check; status after same-day fixes:

1. ~~`tests/test_svi.py` absolute path~~ — FIXED 2026-11-20.
2. **Skew artifact for RQ3** (plan-09 round 3, item 2) — PRD §9.3 skew
   (≈ +0.08 IV left-minus-right at the longest expiry) must be computed and
   cited in `report/report.md`.
3. ~~Negative-rate American put bound~~ — FIXED 2026-11-20 (incl. the
   σ = SIGMA_HI exact-price NO-BRACKET boundary defect the fix exposed).
4. ~~`get_cleaning_rules` ROOT default~~ — FIXED 2026-11-20 (default now
   `ROOT / "config"`; YAML actually read).
5. ~~Near-expiry `0.0 < abs(iv - sigma)`~~ — FIXED 2026-11-23
   (exact recovery allowed; 39 roundtrip tests green).
6. **Missing deliverables this task already owns:** `scripts/run_pipeline.py`
   (Makefile `all`), `scripts/make_figures.py`, `scripts/make_report.py`,
   `report/report.md`, `report/summary.md`, `tests/test_reproducibility.py`,
   clean-clone run + `results/run_metadata.json`, tag `v1.0`.

## Post-v1.0 decisions (2026-11-22)

1. **Directional model: not built.** The 5-day SPY up/down call is near a
   coin flip; any high-accuracy backtest would be leakage. If one is ever
   added it serves as a negative control (expected ≈ 50%) and is never
   presented as a signal. The defensible edge story is the VRP extension
   instead (`extensions/vrp/`).
2. **VRP extension shipped** in `extensions/vrp/` (out of `results/`): mean
   gap +3.75 vol points 2018–now, 95% bootstrap CI [2.03, 5.35], positive
   in 82% of non-overlapping 21-day windows; 2018 alone ~0, 2020 CI wide.
3. **Daily snapshot collection live**: Windows scheduled task weekdays
   15:45 runs `scripts/daily_snapshot.ps1` (fetch → checksum → commit →
   push). 2026-11-22 snapshot already collected. History accrues for a
   future backtest.
4. **Clean-clone test PASS** (results/run_metadata.json): clone → venv →
   pinned install → pipeline → 1315 tests green.
5. **v1.0 tagged and pushed.**
