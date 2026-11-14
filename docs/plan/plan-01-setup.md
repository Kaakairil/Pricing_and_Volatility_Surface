---
description: Task 1 — repo scaffold, pyproject, make, config
---

# Task 1: Repo Setup

Implements: PRD §10 (NFR), §11 (structure).

## Steps

1. Create `pyproject.toml` (Python ≥3.11, setuptools, deps pinned: numpy, scipy, pandas, yfinance, matplotlib, pytest, ruff, pyyaml). Use `[project]` + `[tool.pytest]`, `[tool.ruff]`.
2. Create `Makefile` with targets: `all` (fetch->clean->check->surface->report), `test`, `lint`, `figures`, `data`.
3. Create `config/market.yaml` (ticker: SPY; rate: 0.04x from snapshot date; dividend: auto/recorded; snapshot date), `config/cleaning.yaml` (PRD §9.5 defaults: spread 50%, min T 7d, moneyness 0.7–1.3, OI/vol threshold), `config/pricing_grid.yaml` (PRD §9.1 grid).
4. Create `.gitignore` (data/raw, data/processed, __pycache__, .venv, results/figures).
5. `src/volsurf/__init__.py` stub. `git init` + commit.

## Verify
- `ruff check .` passes, `python -c "import volsurf"` works after `pip install -e .`
