---
description: Task 5 — implied volatility inversion
---

# Task 5: Implied Volatility (FR-5)

## Files
- `src/volsurf/implied_vol.py`, `tests/test_implied_vol_roundtrip.py`

## Interfaces
- `implied_volatility(S, K, T, market_price, r, q, option) -> (sigma, reason)` — returns `(nan, code)` for out-of-bounds; codes: `LOW-NA` (< intrinsic), `HIGH-NA` (> upper bound), `ok` else.

## Steps
- [ ] Write tests: vol grid {0.05,0.1,0.2,0.4} × strikes (deep ITM/OTM included) round-trips to 1e-6; out-of-bounds prices return nan + correct code; near-expiry (T=0.008) case; late round-trips.
- [ ] Implement: bracket [0, 5] with Brent (`scipy.optimize.brentq`, primary); Newton with vega (secondary) on interior bracket with confirmed convergence; explicit bounds before solving per §6.3.
- [ ] `pytest tests/` green; ruff; commit.
