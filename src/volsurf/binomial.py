"""Cox-Ross-Rubinstein binomial tree pricing (European and American).

The tree is vectorized with NumPy: terminal payoffs are evolved backward
one step at a time, taking the max with intrinsic value when american=True.
"""

from __future__ import annotations

import math

import numpy as np

from volsurf.bsm import _validate


def binomial_price(
    S: float,
    K: float,
    T: float,
    sigma: float,
    r: float,
    q: float,
    option: str,
    steps: int = 1000,
    american: bool = True,
) -> float:
    """Price a European or American option with a CRR binomial tree.

    Parameters
    ----------
    S : float
        Spot price.
    K : float
        Strike price.
    T : float
        Time to expiry in years.
    sigma : float
        Volatility (decimal).
    r : float
        Continuously compounded risk-free rate.
    q : float
        Continuously compounded dividend yield.
    option : str
        "call" or "put".
    steps : int
        Number of tree steps.
    american : bool
        If True, allow early exercise (American); else European.
    """
    _validate(S, K, T, sigma, r, q, option)
    if steps < 1:
        raise ValueError(f"steps must be >= 1, got {steps}")

    dt = T / steps
    u = math.exp(sigma * math.sqrt(dt))
    d = 1.0 / u
    disc = math.exp((r - q) * dt)
    if not (d < disc < u):
        raise ValueError(
            f"invalid tree: d={d:.6f}, e^((r-q)dt)={disc:.6f}, u={u:.6f}; "
            "risk-neutral probability outside [0,1] (short expiry or low volatility)"
        )
    p = (disc - d) / (u - d)

    # Precompute powers once, so each backward step is an array slice, no exp per node.
    u_pow = u ** np.arange(steps + 1, dtype=float)
    d_pow = d ** np.arange(steps + 1, dtype=float)

    # Terminal asset prices: S * u^k * d^(N-k), k = 0..N
    s_t = S * u_pow * d_pow[steps::-1]

    if option == "call":
        value = np.maximum(s_t - K, 0.0)
    else:  # put
        value = np.maximum(K - s_t, 0.0)

    disc_steps = math.exp(-r * dt)

    if american:
        for k in range(steps - 1, -1, -1):
            s_node = S * u_pow[: k + 1] * d_pow[k::-1]
            continuation = disc_steps * (p * value[1 : k + 2] + (1 - p) * value[: k + 1])
            intrinsic = (
                np.maximum(s_node - K, 0.0)
                if option == "call"
                else np.maximum(K - s_node, 0.0)
            )
            value = np.maximum(continuation, intrinsic)
        return float(value[0])

    # European: sum terminal payoff weighted by binomial probabilities, discount once
    ks = np.arange(steps + 1, dtype=float)
    binom = np.array([math.comb(steps, int(k)) for k in ks], dtype=float)
    prob = binom * (p ** ks) * ((1 - p) ** (steps - ks))
    return float(np.sum(prob * value) * math.exp(-r * T))
