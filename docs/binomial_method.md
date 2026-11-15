# CRR Binomial Method Notes

## Model

Cox-Ross-Rubinstein tree: divide `[0, T]` into N steps of length `dt = T/N`.

- Up factor: `u = exp(σ √dt)`
- Down factor: `d = 1/u`
- Risk-neutral (continuous dividend `q`) probability: `p = (e^{(r−q)dt} − d) / (u − d)`

**Validity:** the tree is only a valid probability space if `d < e^{(r−q)dt} < u`.
When that fails (very short expiries at low volatility, or tiny step counts),
the function raises `ValueError` rather than returning a bogus price.

## Pricing

Terminal payoffs `payoff(S_T)` at the `N+1` nodes, then backward induction:

- European: expected discounted terminal payoff under the binomial
  probabilities, discounted once by `e^{−rT}`.
- American: at each node take `max(continuation, intrinsic)` so early
  exercise is captured.

All asset-price powers are precomputed once (`u^k`, `d^k` arrays), so each
backward step is an array slice + multiply — no per-node `exp`.

## Runtime

Measured on this machine (Python 3.12, Windows 11):

- 1000-step American call, one price: **~25 ms** (10-run average).
- Reference 10,000-step American price (used only in the convergence test,
  marked slow): dominates the binomial test runtime.
