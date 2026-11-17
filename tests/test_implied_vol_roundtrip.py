"""Implied-volatility inversion tests (Task 05).

Round-trip sigma for European (Black-Scholes) and American (binomial)
options, out-of-bounds reason codes, and near-expiry behavior.
"""

import math

import numpy as np
import pytest

from volsurf.binomial import binomial_price
from volsurf.bsm import black_scholes
from volsurf.implied_vol import implied_volatility

GRID = [
    (100, 100, 1.0, 0.1, 0.05, 0.02),
    (100, 100, 0.25, 0.2, 0.05, 0.02),
    (100, 110, 0.5, 0.4, 0.04, 0.015),
    (90, 100, 0.08, 0.2, 0.05, 0.02),
]

# Deep ITM/OTM strikes (moneyness 0.8 / 1.2), traded third Friday only.
DEEP_STRIKES = [(80, "call"), (120, "put"), (120, "call"), (80, "put")]


class TestEuropeanRoundTrip:
    @pytest.mark.parametrize("S,K,T,sigma,r,q", GRID)
    @pytest.mark.parametrize("option", ["call", "put"])
    def test_recovers_sigma(self, S, K, T, sigma, r, q, option):
        price = black_scholes(S, K, T, sigma, r, q, option)
        iv, reason = implied_volatility(S, K, T, price, r, q, option, style="european")
        assert reason == "ok"
        assert abs(iv - sigma) < 1e-6

    @pytest.mark.parametrize("sigma", [0.1, 0.2, 0.4])
    def test_deep_itm_and_otm(self, sigma):
        S, T, r, q = 100.0, 0.25, 0.05, 0.02
        for K, option in DEEP_STRIKES:
            price = black_scholes(S, K, T, sigma, r, q, option)
            iv, reason = implied_volatility(S, K, T, price, r, q, option, style="european")
            assert reason == "ok", (K, option, sigma)
            assert abs(iv - sigma) < 1e-5


class TestAmericanRoundTrip:
    @pytest.mark.parametrize("sigma", [0.3, 0.4])
    def test_deep_itm_and_otm(self, sigma):
        # Deep-ITM American options with q > 0 price above the discounted
        # European intrinsic and (calls) can exceed S e^{-qT}; the American
        # bounds (lower = undiscounted intrinsic, upper = S) must accept the
        # price and the inversion must recover sigma (plan-05 gap audit).
        # sigma >= 0.3 keeps every strike above the intrinsic plateau where
        # IV would be non-identifiable (documented below).
        S, T, r, q = 100.0, 0.25, 0.05, 0.02
        for K, option in DEEP_STRIKES:
            price = binomial_price(S, K, T, sigma, r, q, option, steps=500, american=True)
            iv, reason = implied_volatility(
                S, K, T, price, r, q, option, style="american", steps=500
            )
            assert reason == "ok", (K, option, sigma)
            assert abs(iv - sigma) < 1e-5

    def test_put_at_intrinsic_is_non_identifiable_not_arbitrage(self):
        # A deep-ITM American put priced exactly at its intrinsic value is
        # flat in sigma below the exercise boundary (no unique IV). It must
        # return NaN with an explicit reason, never a fabricated sigma.
        S, K, T, r, q = 100.0, 120.0, 0.25, 0.05, 0.02
        iv, reason = implied_volatility(S, K, T, K - S, r, q, "put", style="american", steps=500)
        assert np.isnan(iv)
        assert reason in ("LOW-NA", "NO-BRACKET")

    @pytest.mark.parametrize("S,K,T,sigma,r,q", GRID)
    @pytest.mark.parametrize("option", ["call", "put"])
    def test_recovers_sigma_with_same_tree(self, S, K, T, sigma, r, q, option):
        for steps in (250, 500):
            price = binomial_price(S, K, T, sigma, r, q, option, steps=steps, american=True)
            iv, reason = implied_volatility(
                S, K, T, price, r, q, option, style="american", steps=steps
            )
            assert reason == "ok"
            # Tree is not smooth at small step counts: allow a modest tolerance.
            assert abs(iv - sigma) < 1e-5


class TestBounds:
    @pytest.mark.parametrize("style", ["european", "american"])
    def test_below_intrinsic_is_low_na(self, style):
        # European call below discounted intrinsic.
        S, K, T, r, q = 100.0, 80.0, 0.25, 0.05, 0.02
        price = (S * math.exp(-q * T) - K * math.exp(-r * T)) * 0.5
        iv, reason = implied_volatility(S, K, T, price, r, q, "call", style=style)
        assert np.isnan(iv)
        assert reason == "LOW-NA"

    def test_above_upper_is_high_na(self):
        # Call price above S e^{-qT}: impossible for any sigma >= 0.
        S, K, T, r, q = 100.0, 100.0, 0.25, 0.05, 0.02
        iv, reason = implied_volatility(
            S, K, T, S * math.exp(-q * T) + 1.0, r, q, "call", style="american"
        )
        assert np.isnan(iv)
        assert reason == "HIGH-NA"


class TestValidation:
    def test_rejects_nonpositive_strike(self):
        with pytest.raises(ValueError):
            implied_volatility(100, 0, 0.25, 5.0, 0.05, 0.02, "call")

    @pytest.mark.parametrize("option", ["straddle", ""])
    def test_rejects_bad_option(self, option):
        with pytest.raises(ValueError):
            implied_volatility(100, 100, 0.25, 5.0, 0.05, 0.02, option)

    @pytest.mark.parametrize("price", [float("nan"), float("inf"), -1.0])
    def test_rejects_nonfinite_or_negative_price(self, price):
        with pytest.raises(ValueError):
            implied_volatility(100, 100, 0.25, price, 0.05, 0.02, "call")

    def test_rejects_bad_style(self):
        with pytest.raises(ValueError, match="style"):
            implied_volatility(100, 100, 0.25, 5.0, 0.05, 0.02, "call", style="exotic")


class TestAmericanBounds:
    @pytest.mark.parametrize(
        "option, S, K, price",
        [("call", 120.0, 100.0, 10.0), ("put", 100.0, 120.0, 10.0)],
    )
    def test_price_below_undiscounted_intrinsic_is_low_na(self, option, S, K, price):
        # American lower bound = undiscounted intrinsic (exercise now), which
        # for deep-ITM with q > 0 exceeds the discounted European intrinsic
        # (deep-ITM: discounted intrinsic is ~0, undiscounted is K-S or S-K).
        # A price between the two was previously misreported NO-BRACKET and
        # must now be LOW-NA.
        T, r, q = 0.25, 0.05, 0.02
        assert price < abs(K - S)  # sanity: price below undiscounted intrinsic
        iv, reason = implied_volatility(S, K, T, price, r, q, option, style="american", steps=500)
        assert np.isnan(iv)
        assert reason == "LOW-NA"

    def test_american_upper_bound_is_dominance_not_discounted(self):
        # American call upper bound is S (dominance), not S e^{-qT}; American
        # put upper bound is K, not K e^{-rT}. A price in (S e^{-qT}, S) must
        # therefore be classified by the S bound, not rejected as HIGH-NA.
        from volsurf.implied_vol import _price_bound

        S, K, T, r, q = 100.0, 90.0, 1.0, 0.05, 0.5
        lo, hi = _price_bound(S, K, T, r, q, "call", "american")
        assert hi == S
        lo_p, hi_p = _price_bound(S, K, T, r, q, "put", "american")
        assert hi_p == K

        # A price just below S is within the legitimate American range and
        # must NOT be flagged HIGH-NA (a price above S still is).
        iv, reason = implied_volatility(S, K, T, 99.0, r, q, "call", style="american")
        assert reason != "HIGH-NA"
        iv2, reason2 = implied_volatility(S, K, T, S + 1.0, r, q, "call", style="american")
        assert np.isnan(iv2)
        assert reason2 == "HIGH-NA"


class TestNearExpiry:
    @pytest.mark.parametrize("option", ["call", "put"])
    def test_near_expiry_roundtrips_or_codes(self, option):
        # ~3 days to expiry; answer must be a valid sigma or a reason code.
        S, K, T, r, q = 100.0, 100.0, 0.008, 0.05, 0.02
        for style in ("european", "american"):
            sigma = 0.2
            price = binomial_price(S, K, T, sigma, r, q, option, steps=200, american=True)
            iv, reason = implied_volatility(S, K, T, price, r, q, option, style=style, steps=200)
            if reason == "ok":
                assert 0.0 < abs(iv - sigma) < 0.05
            else:
                assert reason in ("LOW-NA", "HIGH-NA", "NO-BRACKET", "NO-CONV")
