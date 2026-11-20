"""Implied-volatility inversion: European (Black-Scholes) and American (binomial).

Never returns a fabricated value: if the market price is outside the
no-arbitrage price range for sigma in [SIGMA_LO, SIGMA_HI] we return
``(nan, reason)`` with an explicit reason code instead.
"""

from __future__ import annotations

import math

from scipy.optimize import brentq

from volsurf.binomial import binomial_price
from volsurf.bsm import _validate, black_scholes

SIGMA_LO = 1e-4
SIGMA_HI = 3.0

_VALID_STYLES = ("american", "european")

REASON_CODES = ("ok", "LOW-NA", "HIGH-NA", "NO-BRACKET", "NO-CONV")


def _price_bound(
    S: float, K: float, T: float, r: float, q: float, option: str, style: str
) -> tuple[float, float]:
    """(lower, upper) no-arbitrage bounds on the option price for sigma >= 0.

    lower: the higher of the discounted European intrinsic and (American
    only) the undiscounted intrinsic — early exercise makes an American
    option worth at least max(S-K, 0) / max(K-S, 0) right now;
    upper: the limit sigma -> infinity (equivalently T -> infinity):
      - European: S e^{-qT} (calls) / K e^{-rT} (puts);
      - American: S (calls) / K (puts) via dominance — the option can never
        exceed the raw underlying (call) or the strike (put), regardless of T.
    """
    eu_lower = (
        max(S * math.exp(-q * T) - K * math.exp(-r * T), 0.0)
        if option == "call"
        else max(K * math.exp(-r * T) - S * math.exp(-q * T), 0.0)
    )
    if style == "american":
        intrinsic = max(S - K, 0.0) if option == "call" else max(K - S, 0.0)
        lower = max(eu_lower, intrinsic)
        # Calls never exceed S (dominance). Puts never exceed K when r >= 0,
        # but at r < 0 the sigma -> infinity limit is K e^{-rT} > K (holding
        # the strike gains carry), so take the larger of the two.
        upper = S if option == "call" else max(K, K * math.exp(-r * T))
    else:
        lower = eu_lower
        upper = S * math.exp(-q * T) if option == "call" else K * math.exp(-r * T)
    return float(lower), float(upper)


def _objective_european(
    sigma: float, S: float, K: float, T: float, r: float, q: float, option: str
) -> float:
    return black_scholes(S, K, T, sigma, r, q, option)


def _american_sigma_floor(T: float, steps: int, r: float, q: float) -> float:
    """Smallest sigma at which the CRR tree is valid.

    The tree requires d < e^{(r-q)dt} < u, i.e. sigma > |r-q| * sqrt(T/steps).
    Below that the risk-neutral probability leaves [0, 1] and ``binomial_price``
    raises ValueError.  The +0.1% margin keeps the bracket strictly inside the
    valid region.
    """
    if T <= 0.0:
        return SIGMA_LO
    return max(SIGMA_LO, 1.001 * abs(r - q) * math.sqrt(T / steps))


def _objective_american(
    sigma: float,
    S: float,
    K: float,
    T: float,
    r: float,
    q: float,
    option: str,
    steps: int,
) -> float:
    # SPY options are American: invert the binomial tree price (Plan 05 B.1),
    # not Black-Scholes.  The binomial price is monotone increasing in sigma
    # on the valid region (both calls and puts gain from volatility).
    return binomial_price(S, K, T, sigma, r, q, option, steps=steps, american=True)


def implied_volatility(
    S: float,
    K: float,
    T: float,
    market_price: float,
    r: float,
    q: float,
    option: str,
    style: str = "american",
    steps: int = 500,
) -> tuple[float, str]:
    """Invert an option price to implied volatility (sigma).

    Parameters
    ----------
    S, K, T, r, q, option :
        As in ``black_scholes`` / ``binomial_price``.
    market_price : float
        Observed option mid price (> intrinsic; a non-negative price may
        still be unrepresentable for sigma <= SIGMA_HI, in which case we
        return ``(nan, reason)``).
    style : {"american", "european"}
        American (default) uses the binomial tree to invert; European uses
        Black-Scholes (for the comparison column in the report).
    steps : int
        Tree steps used only for the American style (binomial pricing, then
        inversion with the *same* step count).

    Returns
    -------
    (sigma, reason) : tuple[float, str]
        ``reason`` is one of ``REASON_CODES``.  ``sigma`` is NaN whenever
        the price is out of the no-arbitrage range or the solver fails to
        converge; it is a finite value otherwise.

    Raises
    ------
    ValueError
        On invalid option/strike/spot/rate/T (delegated to ``_validate``),
        non-numeric market price, or unknown ``style``.
    """
    _validate(S, K, T, 0.5, r, q, option)
    if style not in _VALID_STYLES:
        raise ValueError(f"style must be one of {_VALID_STYLES}, got {style!r}")
    if not isinstance(market_price, (int, float)):
        raise ValueError(f"market_price must be a number, got {market_price!r}")
    if not math.isfinite(market_price) or market_price < 0.0:
        raise ValueError(f"market_price must be finite and >= 0, got {market_price!r}")
    if steps < 1:
        raise ValueError(f"steps must be >= 1, got {steps}")

    lower, upper = _price_bound(S, K, T, r, q, option, style)
    if market_price < lower:
        return float("nan"), "LOW-NA"
    if market_price > upper:
        return float("nan"), "HIGH-NA"

    # Both calls and puts are monotone *increasing* in sigma (vega is positive
    # for either side), so a single brentq branch works for both.  The hedge
    # local (sigma_lo) is raised to the tree-validity floor for the American
    # style; it remains SIGMA_LO for the European (Black-Scholes) style.
    sigma_lo = _american_sigma_floor(T, steps, r, q) if style == "american" else SIGMA_LO
    if sigma_lo >= SIGMA_HI:
        return float("nan"), "NO-BRACKET"
    f_lo = _objective(sigma_lo, S, K, T, r, q, option, steps, style) - market_price
    f_hi = _objective(SIGMA_HI, S, K, T, r, q, option, steps, style) - market_price
    if f_hi == 0.0:
        # Price exactly at the sigma_hi objective: sigma == SIGMA_HI, no
        # bracket needed (a strict `0 < f_hi` would misreport NO-BRACKET).
        return float(SIGMA_HI), "ok"
    if f_lo < 0 < f_hi:
        # The price objective is monotone increasing, smooth, and already
        # bracketed; brentq converges quickly and accurately.
        try:
            sigma = brentq(
                lambda s: _objective(s, S, K, T, r, q, option, steps, style) - market_price,
                sigma_lo,
                SIGMA_HI,
            )
        except (ValueError, RuntimeError):
            return float("nan"), "NO-CONV"
        return float(sigma), "ok"
    return float("nan"), "NO-BRACKET"


def _objective(
    sigma: float,
    S: float,
    K: float,
    T: float,
    r: float,
    q: float,
    option: str,
    steps: int,
    style: str,
) -> float:
    if style == "european":
        return _objective_european(sigma, S, K, T, r, q, option)
    return _objective_american(sigma, S, K, T, r, q, option, steps)
