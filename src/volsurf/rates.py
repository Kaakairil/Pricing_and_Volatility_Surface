"""Discount-rate and dividend-yield conversions (Task 06, PRD §16, B.3).

The 3-month Treasury discount rate (FRED DTB3) is quoted as a *bank
discount* yield on a 360-day basis.  We convert it to a continuously
compounded annual rate on the actual 91-day tenor:

    P = 1 - d * days / 360          (price per $1 par, bank-discount convention)
    r = -ln(P) * 365 / days         (continuous compounding)

The dividend yield reported by Yahoo is a trailing 12-month amount per
share.  With a per-share trailing amount `y` and spot `S`, the discrete
yield is `Y = y / S` and the continuous dividend yield is `q = ln(1 + Y)`
(the continuous rate that produces the same total return over one
horizon as a discrete dividend of `Y` per period).
"""

from __future__ import annotations

import math


def risk_free_from_dtb3(discount_rate: float, tenor_days: int = 91) -> float:
    """Convert a DTB3 bank-discount yield to a continuous annual rate.

    Parameters
    ----------
    discount_rate : float
        DTB3 quote as a decimal (e.g. 0.0414 for 4.14%).
    tenor_days : int
        Actual days to maturity (default 91 for the 3-month T-bill).

    Returns
    -------
    float
        Continuously compounded annual risk-free rate.
    """
    if (
        not math.isfinite(discount_rate)
        or discount_rate < 0.0
        or discount_rate >= 1.0
        or tenor_days <= 0
    ):
        raise ValueError(
            f"discount_rate in [0, 1) and tenor_days > 0 required, got "
            f"(discount_rate={discount_rate!r}, tenor_days={tenor_days!r})"
        )
    price = 1.0 - discount_rate * tenor_days / 360.0
    if price <= 0.0:
        raise ValueError(f"discount_rate {discount_rate} drives bill price to zero or below")
    return -math.log(price) * 365.0 / tenor_days


def dividend_yield_continuous(trailing_12m_dividends: float, spot: float) -> float:
    """Convert a trailing 12-month dividend amount to a continuous yield q.

    Parameters
    ----------
    trailing_12m_dividends : float
        Total dividends paid per share over the last 12 months (decimal).
    spot : float
        Current underlying spot price (> 0).

    Returns
    -------
    float
        Continuous dividend yield q = ln(1 + trailing / spot).
    """
    if not math.isfinite(trailing_12m_dividends) or trailing_12m_dividends < 0.0:
        raise ValueError(
            f"trailing_12m_dividends must be finite and >= 0, got {trailing_12m_dividends!r}"
        )
    if not math.isfinite(spot) or spot <= 0.0:
        raise ValueError(f"spot must be finite and > 0, got {spot!r}")
    if trailing_12m_dividends == 0.0:
        return 0.0
    discrete = trailing_12m_dividends / spot
    return math.log(1.0 + discrete)
