---
description: Task 8 — no-arbitrage checks
---

# Task 8: No-Arbitrage Checks (FR-8)

## Files
- `src/volsurf/arbitrage.py`, `tests/test_arbitrage_checks.py`

## Interfaces
- `run_checks(df, spot, r, q, tol) -> report DataFrame` — per check: {check, violations, sample}.
- Checks (§6.6): put-call parity (|C−P−(S e^{−qT}−K e^{−rT})| > spread-tol), strike monotonicity (calls ↓K, puts ↑K), convexity/butterfly (call prices convex in K), calendar monotonicity (total var = IV²T non-decreasing in T at fixed moneyness).

## Steps
- [ ] Tests (synthetic, known violations): each check flags its engineered violation; clean monotonic chain passes; parity holds within a wide-enough tolerance on mid prices.
- [ ] Implement: group by expiry for per-slice checks, pair calls/puts by strike for parity; butterfly via second-difference of straddle or call prices.
- [ ] Run on cleaned snapshot, write `results/arbitrage_report.csv` (before+after cleaning). Commit.
