---
description: Task 3 — CRR binomial tree
---

# Task 3: CRR Binomial (FR-3)

## Files
- `src/volsurf/binomial.py`, `tests/test_binomial_convergence.py`

## Interfaces
- `binomial_price(S, K, T, sigma, r, q, option, steps, american=True) -> float`
- Vectorized NumPy tree; `steps` default 1000.

## Steps
- [ ] Write tests: European binomial (500 steps) matches `black_scholes` within 0.01 across PRD §9.1 grid; American ≥ European; American convergence — error at 1000 steps < 0.005 vs 10000-step ref; premium (Am–Eu) rises with rate for puts, ~0 for calls on q=0 stock.
- [ ] Implement CRR: u=exp(sigma sqrt(dt)), d=1/u, p as risk-neutral prob. Backward induction with early-exercise max when american.
- [ ] `pytest tests/` green; ruff; commit.
