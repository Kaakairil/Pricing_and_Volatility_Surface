---
description: Task 12 — report + reproducibility
---

# Task 12: Report, README, make all (G7)

## Files
- `README.md`, `Makefile` finalize, `report/report.md`, 1-page summary

## Steps
- [ ] Write derivation notes in `docs/` if any missing (bsm, binomial, implied_vol, surface, svi).
- [ ] `Makefile all` wiring: data → clean → arbitrage → surface → figures → report; `test`, `lint` targets.
- [ ] `pytest tests/` 85%+ coverage on pricing+IV modules (`coverage run pytest --cov=volsurf.bsm,binomial,montecarlo,implied_vol`).
- [ ] `README.md`: quickstart, `make all` from clean clone, environment, structure tree, links to report.
- [ ] Write `report/report.md` (6–10 pp) with RQ answers + figures; 1-page summary.
- [ ] Clean-clone test: fresh clone → `make all` passes; record package versions + data date.
- Commit.
