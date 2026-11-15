"""Monte Carlo pricing of a European option under geometric Brownian motion.

Two variance reducers:
- **Antithetic variates**: each pair (Z, -Z) is one independent unit, so
  pairs halve the variance contribution of the idiosyncratic draw.
- **Control variate** on the discounted share, X = e^{-rT} S_T with
  mean E[X] = S e^{-qT}: beta = Cov(Y, X)/Var(X) estimated on the same
  paths, then the adjusted estimator Y_bar - beta (X_bar - S e^{-qT}).

The control only helps when X is correlated with the discounted payoff Y
(strongly so for calls); it stays on by default.
"""

from __future__ import annotations

import math

import numpy as np

from volsurf.bsm import _validate


def monte_carlo_price(
    S: float,
    K: float,
    T: float,
    sigma: float,
    r: float,
    q: float,
    option: str,
    paths: int = 200_000,
    seed: int = 0,
    antithetic: bool = True,
    control: bool = True,
) -> tuple[float, float]:
    """Price a European option by Monte Carlo GBM simulation.

    Returns
    -------
    (price, standard_error) : tuple[float, float]
        Price and SE of the point estimator, after the selected variance
        reduction. The SE is the sample SE of the estimator itself, so a
        larger paths count or better control shrinks it.
    """
    _validate(S, K, T, sigma, r, q, option)
    if paths < 1:
        raise ValueError(f"paths must be >= 1, got {paths}")

    rng = np.random.default_rng(seed)
    n = paths if not antithetic else paths // 2
    if n < 1:
        n = 1
    z = rng.standard_normal(n)
    if antithetic:
        z = np.concatenate([z, -z])
    z = z.astype(np.float64)

    drift = (r - q - 0.5 * sigma * sigma) * T
    s_t = S * np.exp(drift + sigma * math.sqrt(T) * z)

    if option == "call":
        payoff = np.maximum(s_t - K, 0.0)
    else:  # put
        payoff = np.maximum(K - s_t, 0.0)

    disc = np.exp(-r * T)
    y = disc * payoff
    if not control:
        return float(y.mean()), float(y.std(ddof=1) / np.sqrt(y.size))

    x = disc * s_t
    x_mean = S * np.exp(-q * T)  # E[disc * S_T]
    beta = np.cov(y, x, ddof=1)[0, 1] / np.var(x, ddof=1)
    adj = y - beta * (x - x_mean)
    return float(adj.mean()), float(adj.std(ddof=1) / np.sqrt(adj.size))
