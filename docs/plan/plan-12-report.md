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
