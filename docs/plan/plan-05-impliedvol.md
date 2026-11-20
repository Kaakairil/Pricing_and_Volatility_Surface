# Task 05: Implied Volatility (American-aware)

**Source:** Master Plan Part E Task 05 (Review B.1) | Implements: FR-5

## Key correction (B.1)
SPY options are American. Invert using the **binomial American price**, not Black-Scholes. Keep Black-Scholes IV as a comparison column to quantify the difference.

## Files
- Create: `src/volsurf/implied_vol.py`, `tests/test_implied_vol_roundtrip.py`, `docs/implied_vol_method.md`

## Interfaces
- `implied_volatility(S, K, T, market_price, r, q, option, style="american", steps=500) -> (sigma, reason)`
- `style`: `"american"` (default, SPY) or `"european"` (comparison / BS column).
- Reason codes: `ok`, `LOW-NA` (below intrinsic bound), `HIGH-NA` (above upper bound), `NO-BRACKET`, `NO-CONV`.

**Bounds (before solving):** lower = style intrinsic; upper = S e^{−qT} (calls), K (American puts), K e^{−rT} (European puts).

## Steps
1. **Tests first:**
   - Round-trip σ ∈ {0.05, 0.1, 0.2, 0.4} across strikes incl. deep ITM/OTM; **European** recover σ within 1e-6.
   - **American** round-trip: price with tree, invert with same tree/steps → within 1e-5 (tree not smooth at small steps).
   - Out-of-bounds → NaN + correct code.
   - Near-expiry T = 0.008 (~3 days): round-trips or returns reason code, never a wrong value.
2. **Implement:** bracket [1e-4, 3.0], `scipy.optimize.brentq` primary; check sign change at both ends first.
3. American: objective = binomial price − mid. Document binomial price monotone ↑ in σ; verify on grid.
4. Newton with vega optional — only if Brent too slow for full chain, and only after convergence confirmed vs Brent; else skip and note in report.
5. Record American IV difference vs Black-Scholes IV for every snapshot option → feeds report.

## Exit criteria
Round-trip tests green; reason codes tested.

## Gap audit updates (2026-11-18)
1. **American no-arbitrage bounds defective.** The lower bound used only the
   *discounted* European intrinsic; deep-ITM American options (q > 0) retain
   the undiscounted intrinsic value via immediate exercise, so prices in
   `[discounted intrinsic, undiscounted intrinsic)` are misreported —
   `NO-BRACKET` instead of `LOW-NA`. The American call upper bound used
   `S e^{-qT}`, but dominance gives `S`; a legitimate deep-ITM American call
   above `S e^{-qT}` is wrongly rejected `HIGH-NA` and a valid round-trip
   fails. Fix the bounds:
   - lower = max(discounted intrinsic, undiscounted intrinsic) for American;
   - upper = `S` (calls) / `K` (puts) for American; unchanged for European.
   Add round-trip tests for deep-ITM American calls with q > 0 and
   classification tests for prices between the two intrinsic values.
2. **Deep-ITM American round-trip coverage:** extend the round-trip grid to
   include moneyness 0.8/1.2 under the American style (the European side
   already covers it) so the fixed bounds are exercised.
3. **Record American-vs-BS IV difference column:** task step 5 lands with the
   surface task (09+); the comparison column is produced there, not here.

## Gap audit round 3 (2026-11-20) — evidence-based re-check

1. **Negative-rate American put upper bound — CONFIRMED BUG — FIXED (2026-11-20).**
   `_price_bound` uses `upper = K` for American puts (implied_vol.py:46,
   "dominance — the option can never exceed the strike"). At r < 0 this is
   wrong: the sigma → ∞ limit of an American put is `K·e^{-r·T} > K`
   (carry *gains* from holding the strike). Reproduced:
   `binomial_price(100, 120, 5.0, 3.0, r=-0.02, q=0.007, put, 500 steps) =
   132.53 > K=120` — a legitimate tree price at σ = 3.0 (the very top of the
   bracket) — and `implied_volatility` returns `(nan, HIGH-NA)` for it. The
   bound must be `max(K, K·e^{-rT})` for r < 0 (equivalently just
   `K·e^{-rT}` when r < 0, `K` when r ≥ 0). Not triggered by SPY snapshots
   (r > 0), so low severity for the report — but it is a real defect in a
   committed library function. **Fix applied:** `upper = max(K, K·e^{-rT})`
   for American puts; regression tests
   (`TestNegativeRatePutBound`) green. A second boundary defect found by
   the same test — a price exactly at the σ = SIGMA_HI objective got
   NO-BRACKET from the strict `f_lo < 0 < f_hi` check — also fixed
   (exact-equality fast path returns σ = SIGMA_HI, reason ok).
2. **r == q tree-degenerate ValueError — FIXED (2026-11-19, Task 09).**
   `_american_sigma_floor` now clamps to ≥ SIGMA_LO
   (implied_vol.py:69); verified inside Task 09's test suite.
3. **Near-expiry test `0.0 < abs(iv - sigma)` — minor, still open.**
   tests/test_implied_vol_roundtrip.py:174 requires the round-trip error to
   be *strictly* positive; an exact recovery (err = 0.0) would fail even
   though exact recovery is the ideal outcome. Cosmetic only (measured err =
   2.5e-4 at T = 0.008); fix in Task 12's test pass.
