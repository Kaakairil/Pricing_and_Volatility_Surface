# Task 03: CRR Binomial Tree

**Source:** Master Plan Part E Task 03 | Implements: FR-3

## Files
- Create: `src/volsurf/binomial.py`, `tests/test_binomial_convergence.py`, `docs/binomial_method.md`

## Interfaces
- `binomial_price(S, K, T, sigma, r, q, option, steps=1000, american=True) -> float`

## Steps
1. **Tests first:**
   - European tree, 500 steps, matches `black_scholes` within 0.01 across PRD §9.1 grid.
   - American ≥ European (tol 1e-10).
   - Convergence: 1000-step American vs 10000-step reference, abs error < 0.005. CRR oscillates with step count — also test average of consecutive counts (999, 1000) shows small oscillation.
   - Call early-exercise premium with q = 0 < 1e-6; put premium nondecreasing in r.
2. **Implement CRR:** dt = T/N, u = e^{σ√dt}, d = 1/u, p = (e^{(r−q)dt} − d)/(u − d).
3. **Validity check:** raise `ValueError` if d < e^{(r−q)dt} < u fails (short expiries, low vol). Test the boundary.
4. Vectorized backward induction (NumPy); American takes max(continuation, intrinsic) per node.
5. Benchmark: 1000 steps for one price < 10 ms; record number.

## Exit criteria
Tests green; runtime recorded.

## Gap audit updates (2026-11-16)
1. **European overflow:** converting `math.comb(N, k)` to float raises `OverflowError` at N >= 5000. Use numerically stable binomial probabilities and add a finite-price test at 10,000 European steps against BSM.
2. **Runtime criterion:** measured 1,000-step American pricing is ~25 ms, above the <10 ms target. Record as unmet or optimize, then update the criterion based on measured evidence; do not report the existing runtime as meeting target.
3. **Cross-method coverage:** PRD §8 requires European binomial-vs-Monte-Carlo agreement. Add a deterministic-seed test at representative grid points with tolerance `0.01 + 3*SE_MC`.
4. **Deterministic boundaries:** specify/test `T == 0` and `sigma == 0`; current CRR validity check rejects these instead of returning deterministic discounted intrinsic value (or a documented validation error).
5. Expand the current four-case European test grid or explicitly label it representative; it does not cover PRD §9.1's full spot × moneyness × maturity × volatility grid.

## Gap audit round 2 (2026-11-18) — status of the 2026-11-16 items
1. European overflow — **done**: probabilities via `scipy.stats.binom.pmf` (log-space stable); 10,000-step finite + BSM agreement test green.
2. Runtime criterion — **done**: `docs/binomial_method.md` now states the <10 ms target is unmet and the recorded ~25 ms supersedes it.
3. Cross-method coverage — **done**: `TestBinomialCrossCheck` in `tests/test_montecarlo.py`, tolerance `0.01 + 3*SE`.
4. Deterministic boundaries — **done**: `T == 0` returns intrinsic; `sigma == 0` raises a documented `ValueError` (chosen path per the audit's "or a documented validation error").
5. Grid labeling — **done**: GRID in `tests/test_binomial_convergence.py` labelled as a representative subset of PRD §9.1 (full cross-product lives in the Greeks FD test).

## Gap audit round 3 (2026-11-20) — re-check
No new gaps. Overflow-safe European probabilities, T = 0 / σ = 0 boundary
behavior, and cross-method agreement all verified in code and tests. The
documented ~25 ms price (vs the master plan's <10 ms target) remains the
recorded runtime; superseding it would need a vectorized rework (not
warranted for this project's scale). No open items.
