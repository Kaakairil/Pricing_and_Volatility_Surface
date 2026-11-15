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

## Gap audit fixes (2026-11-16)
1. **European overflow:** the European branch converts `math.comb(N, k)` to float and
   raises `OverflowError` for N >= 5000 (verified). Compute probabilities in log space
   (`scipy.stats.binom.pmf` or `lgamma`) instead. Add a regression test at `steps=10_000`,
   `american=False` that returns a finite price close to Black-Scholes.
2. **Runtime target missed:** measured 1000-step American = ~25 ms vs the 10 ms target.
   Either revise the target to what the implementation achieves, or cut the cost
   (e.g. build the tree on log-moneyness and avoid the per-step `u_pow * d_pow` product).
   Record the decision in `docs/binomial_method.md`.
3. **Cross-check with Monte Carlo (PRD §8):** add a test that European binomial and Monte
   Carlo agree within the combined tolerance `3 * SE_MC + 0.01` at 3 grid points.
