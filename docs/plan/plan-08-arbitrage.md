# Task 08: No-Arbitrage Checks (American-aware)

**Source:** Master Plan Part E Task 08 (Review B.1) | Implements: FR-8

## Key correction (B.1)
Put-call parity is an equality only for European options. SPY is American → use American parity **bounds**, not the equality.

## Files
- Create: `src/volsurf/arbitrage.py`, `tests/test_arbitrage_checks.py`, `docs/american_parity_bounds.md`

## Interfaces
- `run_checks(df, spot, r, q, tol) -> DataFrame` — columns: check, expiry, violations, sample
- `implied_forward(df, expiry, r, T) -> (forward, n_pairs)`

## Checks
1. **Put-call parity (American bounds):** conservative pair S e^{−qT} − K ≤ C − P ≤ S − K e^{−rT}. **Validate bounds numerically against the binomial pricer on synthetic data before use.** Never the European equality.
2. **Strike monotonicity:** per expiry, call mids ↓ in K, put mids ↑ in K.
3. **Convexity (butterfly):** per expiry, call mids convex in K — second difference across three adjacent strikes ≥ 0, tolerance = half bid-ask spread at middle strike.
4. **Calendar monotonicity:** at fixed log-moneyness k, total variance w = IV²·T nondecreasing in T; interpolate IV at fixed k across expiries first.
5. **Forward consistency (extra):** parity-implied forward ≈ S e^{(r−q)T} within tolerance; report implied q per expiry as dividend cross-check.

## Steps
1. **Tests first** — synthetic chains with one planted violation per check; each flags its violation; clean chain passes.
2. Test American parity bounds on binomial-priced synthetic chains — all bounds must hold for tree prices; document any failure.
3. Implement per-expiry; pair calls/puts by strike.
4. Run before (raw) and after (cleaned) cleaning; write `results/arbitrage_report.csv` side by side.
5. Report violation counts + samples honestly; residual violations after cleaning are a finding.

## Exit criteria
Planted-violation tests green; American bounds validated; report written.
