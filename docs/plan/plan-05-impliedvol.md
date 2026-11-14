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
