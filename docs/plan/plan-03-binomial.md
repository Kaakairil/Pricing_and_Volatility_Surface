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
