"""Monte Carlo pricing of a European option under geometric Brownian motion.

Two variance reducers:
- **Antithetic variates**: each pair (Z, -Z) is one independent unit; the
  estimator and its standard error are computed on the `n` pair means, not
  the `2n` individual draws.
- **Control variate** on the discounted share, X = e^{-rT} S_T with known
  mean E[X] = S e^{-qT}: beta = Cov(Y, X)/Var(X) estimated on the same
  paths, then the adjusted estimator Y_bar - beta (X_bar - S e^{-qT}).

`paths` is the *total* number of simulated paths. With `antithetic=True` it
must be even; the `paths // 2` pairs are the independent sample units. When
the control is degenerate (zero control variance, e.g. T = 0 or sigma = 0)
the control is skipped and the raw estimator is returned with SE 0.
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
        reduction. The SE is the sample SE (ddof=1) across the independent
        units (draws, or antithetic pair means), so a larger effective
        sample size or better control shrinks it.
    """
    _validate(S, K, T, sigma, r, q, option)
    if paths < 2:
        raise ValueError(f"paths must be >= 2 to estimate a standard error, got {paths}")
    if antithetic and paths % 2 != 0:
        raise ValueError(f"antithetic paths require an even count, got {paths}")

    rng = np.random.default_rng(seed)
    n = paths // 2 if antithetic else paths
    z = rng.standard_normal(n).astype(np.float64)
    if antithetic:
        z = np.concatenate([z, -z])

    drift = (r - q - 0.5 * sigma * sigma) * T
    s_t = S * np.exp(drift + sigma * math.sqrt(T) * z)

    if option == "call":
        payoff = np.maximum(s_t - K, 0.0)
    else:  # put
        payoff = np.maximum(K - s_t, 0.0)

    disc = np.exp(-r * T)
    y = disc * payoff
    x = disc * s_t
    x_mean = S * np.exp(-q * T)  # E[disc * S_T]

    if antithetic:
        # Pair means are the independent units: average mirrored residuals.
        y = (y[:n] + y[n:]) / 2.0
        x = (x[:n] + x[n:]) / 2.0

    if not control:
        return float(y.mean()), float(y.std(ddof=1) / np.sqrt(n))

    var_x = np.var(x, ddof=1)
    if var_x <= 0.0:
        # Degenerate control (T == 0, sigma == 0): nothing to adjust, SE is 0.
        return float(y.mean()), 0.0

    beta = np.cov(y, x, ddof=1)[0, 1] / var_x
    adj = y - beta * (x - x_mean)
    return float(adj.mean()), float(adj.std(ddof=1) / np.sqrt(n))
