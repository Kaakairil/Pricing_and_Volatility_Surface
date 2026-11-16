# Implied Volatility Notes

## Model

For an observed market price `V_mkt` and a reference pricing function
`price_func(S, K, T, sigma, r, q, option) -> float`, the implied
volatility is the unique `sigma*` in `[SIGMA_LO, SIGMA_HI]` solving

```
price_func(S, K, T, sigma*, r, q, option) - V_mkt = 0
```

The pricing function is strictly increasing in sigma (positive Vega for
both calls and puts), so the root is unique on the bracket.  SPY options
are **American**: the reference `price_func` for `style="american"`
(default) is the CRR binomial tree (`binomial_price`, `american=True`);
for `style="european"` it is Black-Scholes `black_scholes` (the
comparison column in the report).

## No-arbitrage price bounds

Before solving we compute the price interval reachable by any
`sigma >= 0`:

| | lower | upper |
|---|---|---|
| call | discounted intrinsic | `S e^{-qT}` |
| American put | discounted intrinsic | `K` (exercise now) |
| European put | discounted intrinsic | `K e^{-rT}` |

If `V_mkt < lower` the price is below intrinsic — return
`(nan, "LOW-NA")`.  If `V_mkt > upper` — return `(nan, "HIGH-NA")`.
No fabricated volatility is ever returned.

## Solver

`scipy.optimize.brentq` on the bracket `[sigma_lo, SIGMA_HI]`, checking
the sign change at both ends first.

- `sigma_lo` is `SIGMA_LO = 1e-4` for the European (Black-Scholes)
  style.
- For the American (binomial) style, `sigma_lo` is raised to the
  tree-validity floor `1.001 * |r - q| * sqrt(T / steps)`: below it the
  CRR condition `d < e^{(r-q)dt} < u` fails and `binomial_price` raises
  `ValueError`.  This floor is tiny (<< 0.01 for SPY parameters), so
  calling it the bracket low end loses nothing.

If no sign change exists the price is unreachable on the bracket —
return `(nan, "NO-BRACKET")`.  If `brentq` fails to converge — return
`(nan, "NO-CONV")`.

Because both calls and puts are monotone increasing in sigma, a single
branch (no negation or put-special-casing) is correct for both.

## Deep ITM / low-volatility flatness

At deep ITM strikes and very small `sigma` the Black-Scholes price is
flat at machine precision (price == intrinsic to float rounding).  The
inversion is then ill-posed: the flat region is unidentifiable from the
price, and a market quote there is genuine noise / redundancy relative
to the model.  This is reported honestly as a reason code or a
recovered sigma equal to the bracket floor, never a fabricated number.
The unit tests therefore round-trip deep ITM/OTM strikes at
`sigma >= 0.1`, where the surface is measurable, and document the
flatness at `sigma <= 0.05`.

## Runtime

Measured on this machine (Python 3.12, Windows 11).  A 500-step
American round-trip (one price + inversion with the same tree) is
dominated by the two `binomial_price` evaluations the bracket check
costs; each is ~12 ms out of the tree's cost budget.  The full 500-step
American round-trip test grid (16 parameter rows, 4 steps x option)
runs in ~0.5 s total.

## Reference

Hull, J. C., *Options, Futures, and Other Derivatives*, 11th ed., Ch. 21
("Determining Implied Volatility"); brentq bracket solving per
Numerical Recipes.
