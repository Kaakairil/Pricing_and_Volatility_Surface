# AGENTS.md — VolSurf Project Guide

## Project purpose

VolSurf is a from-scratch Python options-pricing library and implied-volatility analysis tool. It prices European and American options by three independent methods (Black-Scholes-Merton closed form, CRR binomial tree, Monte Carlo with variance reduction), inverts Black-Scholes to implied volatility, cleans a real SPY option chain, and builds a volatility surface with no-arbitrage checks. This is not a trading strategy: do not add live trading, execution, or profitability claims unless the PRD changes.

`PRD_volsurf.md` is the source of truth for research scope, definitions, experimental requirements, and deliverables. When this guide conflicts with the PRD, follow the PRD and update this guide if needed. Keep recommendations and reports evidence-based; state limitations and inconclusive results clearly. Every number in the report must trace to a test, a generated CSV, or a figure.

## Repository and environment

- Python 3.11 or newer.
- Package code lives in `src/volsurf/`; tests in `tests/`; notebooks in `notebooks/`; derivation notes and task plans in `docs/`; generated results and figures under `results/`.
- Use a project-local Python environment when working in this checkout. It is local tooling and must remain excluded from Git.
- Runtime and development dependencies are declared in `pyproject.toml` (numpy, scipy, pandas, yfinance, matplotlib, pytest, ruff, pyyaml) and pinned. Do not add a dependency when the standard library or an installed dependency covers the need.
- Run commands from the repository root. Available Make targets are defined in `Makefile`:

```bash
make test
make lint
make data
make clean
make check
make surface
make figures
make all
```

For focused work, run the relevant test file or script directly. `make all` regenerates the full pipeline (data snapshot, cleaning, no-arbitrage checks, surface, figures, report); it may require network access and take time. Do not run it just to validate an unrelated code change.

## Standards for this project

- **No silent NaN.** Every public function validates inputs (positive spot, strike, maturity; volatility in a plausible range). Pricing or IV-inversion failures return NaN with a reason code, never a fabricated value. The implied-volatility solver uses Brent (primary) then Newton with vega (secondary); explicit no-arbitrage bounds before solving.
- **Numerical discipline.** Every pricer is cross-checked against at least one other method. Verification tolerances are pinned in the PRD §8: BS vs binomial < 0.01 absolute; BS within 3 standard errors of Monte Carlo; binomial American convergence error at 1000 steps < 0.005 vs the 10000-step reference; put-call parity to machine precision (model); Greeks vs central finite differences < 1e-4 relative; IV round-trip recovers σ to 1e-6.
- **Type hints and docstrings** on public functions; `ruff` for linting; `pytest` for tests; at least 85% test coverage on the pricing and implied-volatility modules (`bsm`, `binomial`, `montecarlo`, `implied_vol`).
- Freeze the underlying and snapshot date in `config/market.yaml` before experiments. Record data provenance; never modify raw data in place.
- Tests are deterministic with fixed seeds and no network access in unit tests; mock external data services and use small synthetic fixtures.

## Data handling

- Underlying: SPY (frozen decision, PRD §16). Single snapshot date for the main analysis.
- Risk-free rate: a single constant in `config/market.yaml`, set from the 3-month Treasury bill rate at the snapshot date, with source and date recorded. Report a ±100 bp sensitivity check.
- Every snapshot is saved with a timestamp and SHA256 checksum plus provenance metadata (ticker, date, fetched-at, package versions); a checksum mismatch raises on reload.
- Cleaning rules apply in PRD §6.5 order; each rule's removal count is recorded and reconciles (raw minus sum of removed equals cleaned).
- No-arbitrage violations are reported honestly, including any that remain after cleaning.
- Raw and processed data, virtual environments, caches, and generated results belong in their configured project directories and must follow `.gitignore`. Do not commit downloaded market data, local environments, credentials, or generated outputs unless the user explicitly requests them and the repository policy permits it.
- Keep experiment outputs under `results/` with reproducibility metadata alongside them. Keep report figures generated from the results rather than hand-editing generated figures.

## Development workflow

1. Read the relevant PRD sections, the target task plan in `docs/plan/`, existing implementation, configuration, and tests before changing behavior. Check repository status and preserve unrelated or in-progress changes.
2. When asked to check or recheck the program, audit implemented behavior against the PRD and task acceptance criteria. Identify concrete gaps, mismatches, and missing tests; distinguish confirmed defects from unimplemented future scope. Do not stop at a superficial status report when the request asks to fix or continue the work.
3. For multi-file or behaviorally significant work, write a focused implementation plan, identify affected modules and acceptance checks, and review the plan against the PRD before editing. Keep small fixes direct.
4. Work in dependency order: configuration and data contracts, core logic, pipeline integration, then scripts and reports. Keep changes scoped and follow existing module patterns.
5. Follow the task plans in dependency order (plan-01-setup through plan-12-report). For each: write the failing test first, run it to confirm it fails, implement the minimal code, run it to confirm it passes.
6. Add or update focused tests alongside behavior changes. Run the narrow test first, then relevant broader tests, Ruff, and any supported checks.
7. Inspect the final diff for scope, correctness, generated files, and accidental data or secret inclusion. Report checks run and remaining gaps clearly. Do not commit or push unless explicitly requested.

## Collaboration preferences

- The user commonly asks for a program review against the PRD, including a gap check, before moving to the next task. Treat this as a request for evidence-based verification, not just a summary of completed files.
- The user prefers work to proceed task by task, with relevant implementation and verification completed before advancing.
- The user asks to check before and after each implementation. Check state before starting a task and verify the result after finishing it.
- Keep communication direct and concise. When prompted to audit, lead with concrete gaps and their impact; when prompted to implement, make the change and report verification results.
- Interpret short follow-up prompts in the context of the current project and prior task, while respecting any explicit instruction to pause, avoid tools, or only provide text.

## Code and tests

- Prefer small, typed functions and standard library or already-installed dependencies. Avoid unrelated refactors and speculative abstractions.
- Add type hints and concise docstrings to public functions. Handle invalid external/configuration inputs explicitly; do not add defensive branches for impossible internal states.
- Use pytest for tests and Ruff for linting. Add focused regression tests for behavior changes, especially out-of-bounds pricing, solver edge cases, cleaning reconciliation, checksum verification, and reproducibility.
- Keep tests deterministic with fixed seeds. Avoid network access in unit tests; mock external data services and use small fixtures.
- Run relevant tests and `ruff check src tests` after code changes. Report existing third-party stub or platform limitations rather than hiding them.
- Do not claim the full pipeline passed unless it was actually run.

## Completion standard

Before finishing, inspect the diff, run focused tests and lint for changed code, and state any checks not run. Do not commit, push, or perform destructive cleanup unless explicitly requested. The repository is remote-linked to `https://github.com/Khairil-12/-Pricing_and_Volatility_Surface.git`; commits are made only when the user asks.
