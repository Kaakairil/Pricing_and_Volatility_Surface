# VolSurf Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build VolSurf from scratch — a Python options-pricing library (BSM, CRR binomial, Monte Carlo), implied-volatility inversion, real SPY option-chain cleaning, volatility surface with no-arbitrage checks, and a report answering RQ1–RQ4.

**Architecture:** 12 tasks in strict dependency order. Each task reads its own brief in `docs/plan/plan-NN-*.md`. Those briefs carry exact interfaces, step-by-step TDD instructions, and PRD citations. This PLAN orchestrates them: it adds the delivery gates and cross-task interfaces the briefs assume but do not spell out.

**Tech Stack:** Python ≥3.11, numpy, scipy, pandas, yfinance, matplotlib, pyyaml, pytest, ruff.

**Spec:** `PRD_volsurf.md` (source of truth), `docs/superpowers/specs/2026-11-14-volsurf-design.md`, plus per-task briefing in `docs/plan/plan-NN-*.md`.

## Global Constraints

- Work on `main` only — no feature branches. Before implementation: push all 13 commits to origin; verify `git status` clean.
- Underlying SPY frozen (PRD §16). Single snapshot date committed to `data/snapshots/`.
- Rate: constant 3-month T-bill (FRED DTB3) at snapshot date → continuous compounding; ±100 bp sensitivity check.
- T in years (days/365); volatility/rate decimals; rates continuously compounded; moneyness K/S; log-moneyness k = ln(K/S).
- Option types `"call"`/`"put"` strings, validated by one helper.
- No silent NaN. Every failure returns NaN with a reason code, never a fabricated value.
- Every stochastic function takes explicit `seed`.
- Tolerances pinned (PRD §8): BS vs binomial < 0.01 absolute; BS within 3 SE of MC; binomial American 1000-step vs 10000-step reference < 0.005; put-call parity to machine precision (model); Greeks vs central finite differences < 1e-4 relative; IV round-trip recovers σ to 1e-6.
- ≥85% test coverage on `bsm`, `binomial`, `montecarlo`, `implied_vol`.
- No new dependencies beyond pyproject pinned set. Tests deterministic (fixed seeds, no network in unit tests; `network`/`slow` pytest markers).

## Review Focus

The PRD implies input classes no task's tests name explicitly; each gets its test in the owning task:

1. **Bad pip install state** — fresh clone, `make all` before `pip install -e .` → import fails with a clear message. → Task 1 exit gate.
2. **Snapshot date ≠ fetch date** — off-hours snapshot silently carries stale quotes. → Task 6: `save_snapshot` refuses mismatch.
3. **American parity as European equality** — SPY is American; equality flags false violations. → Task 8: parity tested against binomial American bounds, never equality.
4. **IV solver near-expiry / deep OTM** — must return reason code, never wrong value. → Task 5: `T=0.008` + deep OTM in grid; out-of-bounds → NaN + code.
5. **Coverage silently missed** — report claims ≥85% from memory. → Task 12: gate runs `pytest --cov`, records per-module numbers.
6. **Run-to-run non-reproducibility** — seeds/ordering/format jitter changes CSVs across runs. → Task 12: pipeline twice → byte-identical CSVs.
7. **Out-of-hull surface extrapolation** — silent extrapolation. → Task 9: out-of-hull grid points are NaN.

---

### Task 1: Repository Setup

**Brief:** `docs/plan/plan-01-setup.md`

**Files:** `pyproject.toml`, `Makefile`, `config/market.yaml`, `config/cleaning.yaml`, `config/pricing_grid.yaml`, `src/volsurf/__init__.py`, `.gitignore`

**Interfaces:**
- Produces: `volsurf` importable package; `make test` / `make lint` / `make all` / `make fetch` targets; config YAMLs consumed by Tasks 6–10.

- [ ] **Step 1: Create source scaffolding and pyproject per brief, TDD-style (test-first where testable)**
- [ ] **Step 2: `pip install -e .`; `python -c "import volsurf"` works; `ruff check .` passes; `pytest` runs clean (zero tests)**
- [ ] **Step 3: Commit**

```bash
git add pyproject.toml Makefile config/ src/volsurf/ .gitignore
git commit -m "task 01: repo scaffold"
```

**Exit gate:** clean venv → `pip install -e .` → `import volsurf` → `make lint` → `pytest`. Review Focus #1 satisfied here.

---

### Task 2: Black-Scholes-Merton Price and Greeks

**Brief:** `docs/plan/plan-02-bsm.md`

**Files:** `src/volsurf/bsm.py`, `tests/test_bsm.py`, `tests/test_greeks_finite_difference.py`, `docs/bsm_derivation.md`

**Interfaces:**
- Produces (consumed by Tasks 3,4,5,8): `black_scholes(S, K, T, sigma, r, q, option) -> float`; Greeks `delta/gamma/vega/theta/rho` same signature.

- [ ] **Step 1: Test-first** — two textbook benchmarks w/ citation; European put-call parity < 1e-10; call ↓K ↑σ ↑T; T=0 / σ=0 edge → intrinsic.
- [ ] **Step 2: RED** — run `pytest tests/test_bsm.py -v`, confirm fails (module missing).
- [ ] **Step 3: Implement** `black_scholes` via `scipy.stats.norm`.
- [ ] **Step 4: GREEN** — full suite; FD Greeks < 1e-4 relative; coverage ≥ 95% on `bsm.py`.
- [ ] **Step 5: Commit** (test + source + docs).

**Exit gate:** `pytest tests/ -k bsm` green; `bash -c "ruff check src/volsurf/bsm.py"` clean.

---

### Task 3: CRR Binomial Tree

**Brief:** `docs/plan/plan-03-binomial.md`

**Files:** `src/volsurf/binomial.py`, `tests/test_binomial_convergence.py`, `docs/binomial_method.md`

**Interfaces:**
- Produces (consumed by Tasks 5,8,10): `binomial_price(S, K, T, sigma, r, q, option, steps=1000, american=True) -> float`.

- [ ] **Step 1: Test-first** — European 500-step vs BS < 0.01 across §9.1 grid; American ≥ European; convergence 1000 vs 10000 steps < 0.005; CRR oscillation check (avg of 999/1000); call premium q=0 < 1e-6; put premium nondecreasing in r.
- [ ] **Step 2: RED** — run, confirm fails.
- [ ] **Step 3: Implement** CRR — dt=T/N, u=e^{σ√dt}, d=1/u, p=(e^{(r−q)dt}−d)/(u−d); vec'd backward induction; `ValueError` if d < e^{(r−q)dt} < u fails.
- [ ] **Step 4: GREEN** — full suite; record 1000-step timing < 10 ms.
- [ ] **Step 5: Commit.**

**Exit gate:** `pytest tests/test_binomial_convergence.py -v` green; timing logged in ledger.

---

### Task 4: Monte Carlo Pricer

**Brief:** `docs/plan/plan-04-montecarlo.md`

**Files:** `src/volsurf/montecarlo.py`, `tests/test_montecarlo.py`

**Interfaces:**
- Produces (consumed by Task 12 RQ1): `monte_carlo_price(S, K, T, sigma, r, q, option, paths=200_000, seed=0, antithetic=True, control=True) -> (price, standard_error)`.

- [ ] **Step 1: Test-first** — BS within 3 SE at 4 grid points; 10 seeds SE ratio 0.7–1.3; control variate reduces SE vs raw.
- [ ] **Step 2: RED** — run, confirm fails.
- [ ] **Step 3: Implement** GBM terminal; antithetic pairs; control variate X = e^{−rT} S_T, β = Cov(Y,X)/Var(X).
- [ ] **Step 4: GREEN** — full suite.
- [ ] **Step 5: Commit.**

**Exit gate:** `pytest tests/test_montecarlo.py -v` green.

---

### Task 5: Implied Volatility (American-aware)

**Brief:** `docs/plan/plan-05-impliedvol.md`

**Files:** `src/volsurf/implied_vol.py`, `tests/test_implied_vol_roundtrip.py`, `docs/implied_vol_method.md`

**Interfaces:**
- Consumes: `black_scholes` (Task 2), `binomial_price` (Task 3).
- Produces (consumed by Tasks 8,9): `implied_volatility(S, K, T, market_price, r, q, option, style="american", steps=500) -> (sigma, reason)`; reason codes `ok`/`LOW-NA`/`HIGH-NA`/`NO-BRACKET`/`NO-CONV`; bounds set per style.

- [ ] **Step 1: Test-first** — European round-trip σ∈{0.05,0.1,0.2,0.4} incl. deep ITM/OTM to 1e-6; American round-trip via same tree to 1e-5; out-of-bounds → NaN + code; `T=0.008` → round-trip or reason, never wrong value (Review Focus #4).
- [ ] **Step 2: RED** — run, confirm fails.
- [ ] **Step 3: Implement** — bracket [1e-4, 3.0]; `scipy.optimize.brentq` primary; sign change check at ends; upper bound S e^{−qT} (calls) / K (American puts).
- [ ] **Step 4: GREEN** — full suite.
- [ ] **Step 5: Commit.**

**Exit gate:** `pytest tests/test_implied_vol_roundtrip.py -v` green; reason codes test in suite.

---

### Task 6: Market Data, Rates, Snapshot

**Brief:** `docs/plan/plan-06-market-data.md`

**Files:** `src/volsurf/market_data.py`, `src/volsurf/rates.py`, `tests/test_market_data.py`, `tests/test_rates.py`

**Interfaces:**
- Produces (consumed by Tasks 7–9,12): `fetch_chain(ticker) -> (options_df, spot, fetch_time_utc)` — `network` marker; `risk_free_from_dtb3(discount_rate, tenor_days=91) -> float`; `save_snapshot(options_df, meta, out_dir) -> Path` (CSV + metadata JSON + SHA256 sidecar); `load_snapshot(path) -> (options_df, meta)` — raises on checksum mismatch.
- `data/snapshots/{snapshot_date}.csv` + `.json` + `.sha256` committed.

- [ ] **Step 1: Test-first** — save/load round-trip exact; tampered CSV raises; metadata fields complete; DTB3 conversion hand-verified.
- [ ] **Step 2: RED** — run, confirm fails.
- [ ] **Step 3: Implement** — P = 1 − d·91/360; r = −ln(P)·365/91; q = ln(1 + y) continuous; raw yfinance IV stored as `yf_iv` comparison-only; `save_snapshot` refuses recorded-date ≠ fetch-date (Review Focus #2).
- [ ] **Step 4: GREEN** + manual `make fetch` during market hours; fill `config/market.yaml`; commit snapshot.
- [ ] **Step 5: Commit.**

**Exit gate:** unit tests green; one committed snapshot reloads + checksum passes; `config/market.yaml` filled.

---

### Task 7: Data Cleaning

**Brief:** `docs/plan/plan-07-cleaning.md`

**Files:** `src/volsurf/cleaning.py`, `tests/test_cleaning_reconciliation.py`

**Interfaces:**
- Consumes: `load_snapshot` (Task 6), `config/cleaning.yaml`.
- Produces (consumed by Tasks 8,9): `clean(df, spot, rules) -> (cleaned_df, removal_log)`; `compute_moneyness(df, spot) -> Series`; `compute_tte(df, snapshot_date) -> Series`.

- [ ] **Step 1: Test-first** — one planted row per rule; each removes exactly its rows; reconciliation raw − Σ(removed) = cleaned; mid = arithmetic mean; band edges 0.7/1.3 kept, just outside removed.
- [ ] **Step 2: RED** — run, confirm fails.
- [ ] **Step 3: Implement** — rules in order (PRD §6.5); thresholds from `config/cleaning.yaml`, never hardcoded; clean-on-copy; log per rule.
- [ ] **Step 4: GREEN** — apply to committed snapshot; write `results/cleaning_report.csv`; keep raw copy.
- [ ] **Step 5: Commit.**

**Exit gate:** `pytest tests/test_cleaning_reconciliation.py -v` green; report CSV written.

---

### Task 8: No-Arbitrage Checks (American-aware)

**Brief:** `docs/plan/plan-08-arbitrage.md`

**Files:** `src/volsurf/arbitrage.py`, `tests/test_arbitrage_checks.py`, `docs/american_parity_bounds.md`

**Interfaces:**
- Consumes: `binomial_price` (Task 3), `implied_volatility` (Task 5), cleaned chain (Task 7).
- Produces (consumed by Task 12 RQ4): `run_checks(df, spot, r, q, tol) -> DataFrame`; `implied_forward(df, expiry, r, T) -> (forward, n_pairs)`.

- [ ] **Step 1: Test-first** — synthetic chain one planted violation per check; each flags its own; clean passes; **American parity bounds validated against binomial-priced synthetic chains** (Review Focus #3).
- [ ] **Step 2: RED** — run, confirm fails.
- [ ] **Step 3: Implement** — 5 checks: American parity bounds (not equality), strike monotonicity, convexity (butterfly), calendar monotonicity at fixed k, forward consistency.
- [ ] **Step 4: GREEN** — run before/after cleaning; write `results/arbitrage_report.csv`; report residual violations honestly.
- [ ] **Step 5: Commit.**

**Exit gate:** planted-violation tests green; American bounds validated; report written.

---

### Task 9: Volatility Surface and Plots

**Brief:** `docs/plan/plan-09-surface.md`

**Files:** `src/volsurf/surface.py`, `src/volsurf/plots.py`, `tests/test_surface.py`, `docs/surface_method.md`

**Interfaces:**
- Consumes: `implied_volatility` (Task 5), cleaned chain (Task 7), `config/cleaning.yaml`.
- Produces (consumed by Task 12 RQ3): `compute_iv_table(df, spot, r, q, style="american") -> DataFrame` (American IV + BS-IV comparison columns, reason codes); `build_surface(iv_table) -> (grid_df, method_info)`; plot fns `plot_smiles`, `plot_term_structure`, `plot_surface_3d`, `plot_error_heatmap`, `plot_pre_post_cleaning`, `plot_iv_american_vs_bs`.

- [ ] **Step 1: Write the failing test** — `tests/test_surface.py`: interpolated surface reproduces input IVs at node points within 1e-8; NaN-IV points dropped before fit with logged count; <5 strikes in slice raises clear error or skips with log entry; out-of-hull grid points are NaN, never extrapolated silently (Review Focus #7).
- [ ] **Step 2: Run test to verify it fails** — `pytest tests/test_surface.py -v`; Expected: FAIL (module missing).
- [ ] **Step 3: Implement** — k = ln(K/S); `scipy.interpolate.LinearNDInterpolator` on (k, T); document C0 and no no-arbitrage guarantee.
- [ ] **Step 4: Run test to verify it passes** — `pytest tests/test_surface.py -v`; Expected: PASS.
- [ ] **Step 5: Generate all figures** from cleaned snapshot under `results/figures/`, incl. American-vs-BS IV comparison.
- [ ] **Step 6: Commit** — `git add tests/test_surface.py src/volsurf/surface.py src/volsurf/plots.py docs/surface_method.md && git commit -m "task 09: volatility surface and plots"`

**Exit gate:** tests green; all figures generated under `results/figures/`.

---

### Task 10: Early-Exercise Premium Experiment

**Brief:** `docs/plan/plan-10-early-exercise.md`

**Files:** `src/volsurf/experiments.py`, `tests/test_experiments.py`

**Interfaces:**
- Consumes: `binomial_price` (Task 3), SPY parameters (Task 6), configured rate (Task 1).
- Produces (consumed by Task 12 RQ2): `early_exercise_premium(S, moneyness, T_grid, sigma, r, q, steps=1000) -> DataFrame` — columns moneyness/T/option/american/european/premium/premium_pct.

- [ ] **Step 1: Write the failing test** — `tests/test_experiments.py`: premium >= -1e-10 all rows; q=0 -> call premium < 1e-6; SPY dividend -> call premium positive for at least one config; put premium nondecreasing in r; no NaN.
- [ ] **Step 2: Run test to verify it fails** — `pytest tests/test_experiments.py -v`; Expected: FAIL (module missing).
- [ ] **Step 3: Implement** — paired American + European binomial over PRD §9.1 grid (moneyness × T × rate ±100bp), sigma = SPY ATM IV from snapshot.
- [ ] **Step 4: Run test to verify it passes** — `pytest tests/test_experiments.py -v`; Expected: PASS.
- [ ] **Step 5: Write outputs** — `results/early_exercise_premium.csv`, `results/rate_sensitivity.csv`; verify no NaN.
- [ ] **Step 6: Commit** — `git add tests/test_experiments.py src/volsurf/experiments.py && git commit -m "task 10: early-exercise premium experiment"`

**Exit gate:** tests green; CSVs written.

---

### Task 11: SVI Slice Fit (stretch)

**Brief:** `docs/plan/plan-11-svi.md`

**Files:** `src/volsurf/svi.py`, `tests/test_svi.py`, `docs/svi_method.md`

**Interfaces:**
- Consumes: cleaned chain + IV table (Tasks 7, 9).
- Produces: `fit_svi_slice(k, total_var, weights=None, x0=None) -> params` ({a, b, rho, m, sigma}); `svi_total_variance(params, k) -> array`; `check_butterfly(params, k_grid) -> (bool, min_g)`.

- [ ] **Step 1: Write the failing test** — `tests/test_svi.py`: synthetic smile w/ known params recovered within 1e-3; constraint violations rejected by fit; engineered violating slice flagged by `check_butterfly`; fitted clean slice passes.
- [ ] **Step 2: Run test to verify it fails** — `pytest tests/test_svi.py -v`; Expected: FAIL (module missing).
- [ ] **Step 3: Implement** — fit on total variance w = IV^2 * T via `scipy.optimize.least_squares` with bounds; constraints enforced during fit (b >= 0, |rho| < 1, sigma > 0, a + b*sigma*sqrt(1-rho^2) >= 0); butterfly density g(k) >= 0 per Gatheral 2014.
- [ ] **Step 4: Run test to verify it passes** — `pytest tests/test_svi.py -v`; Expected: PASS.
- [ ] **Step 5: Fit 2-3 cleaned expiries, >= 5 strikes each** — `results/svi_fit.csv` (params, fit RMSE, butterfly result); SVI-vs-interpolated figure.
- [ ] **Step 6: Commit** — `git add tests/test_svi.py src/volsurf/svi.py docs/svi_method.md && git commit -m "task 11: SVI slice fit"
Stretch note: start after Task 10 + report draft. If time runs out: skip, state out of scope in report.

**Exit gate:** tests green; fits + figure produced (or explicitly deferred w/ report note).

---

### Task 12: Report, README, Reproducibility

**Brief:** `docs/plan/plan-12-report.md`

**Files:** `README.md` (finalize), `Makefile` (final), `report/report.md`, `report/summary.md`, `tests/test_reproducibility.py`

**Interfaces:**
- Consumes: everything — pricer agreement (Tasks 2-4), premium (Task 10), surface (Task 9), arbitrage (Task 8), snapshot (Task 6).

- [ ] **Step 1: Finalize Makefile** — `all` = committed snapshot -> clean -> arbitrage -> surface -> experiments -> figures -> report (no network); `fetch` manual/live/network, not part of `all`; `test` = `pytest -m "not network"` w/ coverage; `lint` = `ruff check . && ruff format --check .`.
- [ ] **Step 2: Coverage gate** — `pytest --cov=volsurf --cov-report=term-missing`; >= 85%% on `bsm`/`binomial`/`montecarlo`/`implied_vol`; record per-module numbers (Review Focus #5).
- [ ] **Step 3: Reproducibility test** — `tests/test_reproducibility.py`: pipeline twice on committed snapshot -> byte-identical CSVs (Review Focus #6); fix nondeterminism (seeds, ordering, float formatting).
- [ ] **Step 4: README** — what project is/is not, quickstart, `make all` < 10 min on committed snapshot, environment, structure tree, data provenance, report + docs links.
- [ ] **Step 5: report/report.md** (6-10 pp) one section per RQ: RQ1 pricer agreement tables + verification grid; RQ2 premium figure/table; RQ3 smile, term structure, 3D surface, American-vs-BS IV comparison; RQ4 arbitrage before/after cleaning w/ honest residuals. Limitations: free data, single snapshot, continuous dividend approximation, linear interpolation (C0), no Heston, rate sensitivity. `report/summary.md` one-page non-specialist.
- [ ] **Step 6: Clean-clone test** — clone into empty dir -> `make setup && make all && make test`; record output + env in `results/run_metadata.json`.
- [ ] **Step 7: Commit; tag v1.0** — `git add README.md Makefile report/ tests/test_reproducibility.py && git commit -m "task 12: report, README, reproducibility" && git tag v1.0`

**Exit gate:** clean-clone run passes; coverage target met; report + summary written; tagged `v1.0` (Heston explicitly out of scope per PRD §16.4).

---

## Execution Notes

- Each task: read the brief first (exact values/signatures live there), then RED-GREEN in the brief's step order. Commit per the brief's file-set.
- Task 11 stretch: pick up after Task 10 + report draft; skip w/ explicit report note if time-boxed.
- Final whole-branch review before tagging (superpowers:requesting-code-review).

## Pre-flight Interface Scan

- Tasks 2->3/4/5: `black_scholes` signature consumed by tree/MC/IV — consistent (S, K, T, sigma, r, q, option).
- Task 3->5/8/10: `binomial_price(..., steps, american)` — IV inverts tree prices (same steps), arbitrage validates bounds, experiments pair american/european — consistent.
- Task 5->8/9: reason-code tuple `(sigma, reason)` consumed for IV table — consistent.
- Task 6->7/8/9: snapshot CSV columns consumed by cleaning (bid/ask/IV/T) — briefs align on schema.
- Task 7->8/9: `(cleaned_df, removal_log)` — consistent.
- No conflicts found.
