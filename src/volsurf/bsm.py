"""Black-Scholes-Merton closed-form pricing and analytical Greeks.

All rates and volatilities are decimals, continuously compounded.
T is in years. Theta is dV/dt = -dV/dT per year (time decay; divide by 365
for per-calendar-day decay).
"""

from __future__ import annotations

import math

from scipy.stats import norm

_VALID_OPTIONS = ("call", "put")
_MAX_SIGMA = 5.0  # plausible-volatility ceiling (PRD §10); 500% is far outside any SPY surface


def _validate(S: float, K: float, T: float, sigma: float, r: float, q: float, option: str) -> None:
    if option not in _VALID_OPTIONS:
        raise ValueError(f"option must be 'call' or 'put', got {option!r}")
    for name, value in (("S", S), ("K", K), ("T", T), ("sigma", sigma), ("r", r), ("q", q)):
        if not isinstance(value, (int, float)):
            raise ValueError(f"{name} must be a number, got {value!r}")
        if not math.isfinite(value):
            raise ValueError(f"{name} must be finite, got {value!r}")
    if S <= 0 or K <= 0:
        raise ValueError(f"spot and strike must be positive, got S={S}, K={K}")
    if T < 0:
        raise ValueError(f"maturity must be non-negative, got T={T}")
    if sigma < 0:
        raise ValueError(f"volatility must be non-negative, got sigma={sigma}")
    if sigma > _MAX_SIGMA:
        raise ValueError(f"volatility above plausible ceiling {_MAX_SIGMA}, got sigma={sigma}")


def _intrinsic(S: float, K: float, T: float, r: float, q: float, option: str) -> float:
    if option == "call":
        return max(S * math.exp(-q * T) - K * math.exp(-r * T), 0.0)
    return max(K * math.exp(-r * T) - S * math.exp(-q * T), 0.0)


def black_scholes(
    S: float, K: float, T: float, sigma: float, r: float, q: float, option: str
) -> float:
    """BSM price of a European option."""
    _validate(S, K, T, sigma, r, q, option)
    if T == 0.0 or sigma == 0.0:
        return _intrinsic(S, K, T, r, q, option)
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    if option == "call":
        return S * math.exp(-q * T) * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)
    return K * math.exp(-r * T) * norm.cdf(-d2) - S * math.exp(-q * T) * norm.cdf(-d1)


def delta(S: float, K: float, T: float, sigma: float, r: float, q: float, option: str) -> float:
    """dV / dS, per unit of spot (unitless, in [0, 1] for calls)."""
    _validate(S, K, T, sigma, r, q, option)
    if T == 0.0 or sigma == 0.0:
        if option == "call":
            return math.exp(-q * T) if S * math.exp(-q * T) > K * math.exp(-r * T) else 0.0
        return -math.exp(-q * T) if K * math.exp(-r * T) > S * math.exp(-q * T) else 0.0
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / (sigma * math.sqrt(T))
    if option == "call":
        return math.exp(-q * T) * norm.cdf(d1)
    return math.exp(-q * T) * (norm.cdf(d1) - 1.0)


def gamma(S: float, K: float, T: float, sigma: float, r: float, q: float, option: str) -> float:
    """d^2 V / dS^2, per unit spot squared (identical for calls and puts)."""
    _validate(S, K, T, sigma, r, q, option)
    if T == 0.0 or sigma == 0.0:
        return 0.0
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / (sigma * math.sqrt(T))
    return math.exp(-q * T) * norm.pdf(d1) / (S * sigma * math.sqrt(T))


def vega(S: float, K: float, T: float, sigma: float, r: float, q: float, option: str) -> float:
    """dV / d sigma, per unit of volatility (1.0 = 100 vol points, not per 1%)."""
    _validate(S, K, T, sigma, r, q, option)
    if T == 0.0 or sigma == 0.0:
        return 0.0
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / (sigma * math.sqrt(T))
    return S * math.exp(-q * T) * norm.pdf(d1) * math.sqrt(T)


def theta(S: float, K: float, T: float, sigma: float, r: float, q: float, option: str) -> float:
    """dV / dt = -dV / dT, per year (Hull Ch. 19 convention); divide by 365 for per-day."""
    _validate(S, K, T, sigma, r, q, option)
    if T == 0.0:
        return 0.0
    if sigma == 0.0:
        f_s = S * math.exp(-q * T)
        f_k = K * math.exp(-r * T)
        if option == "call":
            return (q * f_s - r * f_k) if f_s > f_k else 0.0
        return (r * f_k - q * f_s) if f_k > f_s else 0.0
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    common = -S * math.exp(-q * T) * norm.pdf(d1) * sigma / (2.0 * math.sqrt(T))
    if option == "call":
        return (
            common
            + q * S * math.exp(-q * T) * norm.cdf(d1)
            - r * K * math.exp(-r * T) * norm.cdf(d2)
        )
    return (
        common - q * S * math.exp(-q * T) * norm.cdf(-d1) + r * K * math.exp(-r * T) * norm.cdf(-d2)
    )


def rho(S: float, K: float, T: float, sigma: float, r: float, q: float, option: str) -> float:
    """dV / dr, per unit of the continuously compounded rate r."""
    _validate(S, K, T, sigma, r, q, option)
    if T == 0.0 or sigma == 0.0:
        f_s = S * math.exp(-q * T)
        f_k = K * math.exp(-r * T)
        if option == "call":
            return K * T * math.exp(-r * T) if f_s > f_k else 0.0
        return -K * T * math.exp(-r * T) if f_k > f_s else 0.0
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    if option == "call":
        return K * T * math.exp(-r * T) * norm.cdf(d2)
    return -K * T * math.exp(-r * T) * norm.cdf(-d2)
