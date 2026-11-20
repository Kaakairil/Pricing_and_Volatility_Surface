# Task 10: Early-Exercise Premium Experiment

**Source:** Master Plan Part E Task 10 (Review B.6) | Implements: RQ2, PRD §9.2

## Status: DONE (2026-11-20)

Pre-implementation gap close (audited 2026-11-20, plan edit first per AGENTS.md):
- **Ownership:** PRD §9.1 multi-method verification grid + Monte-Carlo seed
  variance is owned by plans 02/03/04 (test-land cross-method agreement, 30
  seeds) — Task 10 targets §9.2 / RQ2 only. No `pricing_verification.csv`
  artifact is produced here; scope stays on early-exercise premium.
- **Figure added** (was missing): PRD §10 requires "early-exercise premium by
  moneyness and maturity" as a report figure → `plot_early_exercise_premium`
  (step 5). CSVs alone are not enough for the report.
- **Test wording fixed:** "near ex-dividend-like" replaced by the exercise
  threshold — the CRR tree uses a continuous dividend yield (no discrete
  ex-date); a call is exercised early only when `q·S > r·K` (K/S < q/r).
  At SPY snapshot parameters (r ≈ 4.22%, q ≈ 0.75%) the threshold is
  K/S < 0.177, so no grid point exercises early and the SPY-parameter call
  premium is legitimately ≈ 0 — q > 0 is necessary, not sufficient. The
  mechanism is tested at q = 0.05 where the threshold is exceeded.
- **SPY ATM sigma pinned** (was a loose "from snapshot"): read the near-term
  ATM IV from `results/iv_table.csv` (k ≈ 0, shortest tte) when present,
  else fall back to a documented 0.20 constant. Never crashes without a
  snapshot.

## Files
- Create: `src/volsurf/experiments.py`, `tests/test_experiments.py`
- Plots: `plot_early_exercise_premium` lives with the experiment (in
  `experiments.py` or imported from `plots.py`), Agg backend, per PRD §10.

## Interfaces
- `early_exercise_premium(S, moneyness, T_grid, sigma, r, q, steps=1000) -> DataFrame` — columns: moneyness, T, option, american, european, premium, premium_pct
- `rate_sensitivity(S, moneyness, T, sigma, r_grid, q, steps=1000) -> DataFrame` — premium vs r (tests §9.2 put/rate pattern); writes `results/rate_sensitivity.csv`
- `plot_early_exercise_premium(df, out_dir)` — grouped line/bar by option and expiry

## Grid (aligned to PRD §9.1)
- Moneyness {0.8, 0.9, 1.0, 1.1, 1.2}
- T ∈ {1 week, 1 month, 3 months, 1 year}
- Rate: base ± 100 bp. Dividend: SPY recorded value. Sigma: SPY ATM implied vol from snapshot (pinned near-term ATM IV, fallback 0.20).

## Note
SPY calls have a **nonzero** early-exercise premium because q > 0 (dividends). This is a model experiment using SPY parameters — separate from market analysis.
*(Corrected during implementation: at the 2026-11-16 snapshot parameters
r ≈ 4.22%, q ≈ 0.75%, the call exercise threshold q·S > r·K requires
K/S < 0.177 — far deeper than any traded SPY strike — so the call premium on
the model grid is ≈ 0. The put premium is the economically meaningful SPY
number: it rises with r and grows with moneyness and maturity.)*

## Steps
1. **Tests first:**
   - premium ≥ −1e-10 for all rows.
   - q = 0 → call premium < 1e-6.
   - With SPY dividend yield, call premium positive for at least one configuration (deep ITM, moneyness 1.2, long T); document why (q > 0, no discrete ex-date needed).
   - Put premium increases with r across sensitivity. Output has no NaN.
2. Implement grid as paired American and European binomial prices (same steps → discretization bias cancels in the difference).
3. Write `results/early_exercise_premium.csv` and `results/rate_sensitivity.csv`.
4. Verify no NaN.
5. Generate `early_exercise_premium` figure (PRD §10) into the results figures dir.

## Exit criteria
Tests green; CSVs + figure written. — **Met 2026-11-20**: 10/10 tests green
(failures seen RED first), suite 1297 passed / coverage 96.61% / ruff clean.
SPY-parameter run (r=4.22%, q=0.75%, σ=0.195): put premium up to 1.86
(moneyness 1.2, 1y), call premium ≈ 0 to machine precision (exercise
threshold K/S < q/r = 0.177 unreachable — plan note corrected above).
Outputs: `results/early_exercise_premium.csv` (40 rows),
`results/rate_sensitivity.csv` (10 rows),
`results/surface/early_exercise_premium.png`.

## Gap audit round 3 (2026-11-20) — findings in this task's own code

1. **No open bugs.** The premium grid, rate sensitivity, and figure all
   verified: premium ≥ 0 (machine-precision floor respected), q = 0 →
   call premium < 1e-6, put premium monotone ↑ in r, no NaN.
2. **Plan-note correction stands (documented above):** the original "SPY
   calls have a nonzero premium" claim was wrong at snapshot parameters —
   the exercise threshold K/S < q/r = 0.177 is unreachable, so the call
   premium is ≈ 0 to machine precision (3.6e-14 max) and the *put* premium
   (up to 1.86) is the economically meaningful SPY number. RQ2's "does it
   match theory?" answer: yes — the premium follows the theory including
   the honest zero-call case.
3. **`rate_sensitivity.csv` is plan-invented (justified):** not in the PRD
   §10 results list, but it is the artifact that evidences §9.2's
   "premium rises with rate" check. Kept; cited in the report.
