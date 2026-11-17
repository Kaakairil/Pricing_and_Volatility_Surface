"""CRR binomial tree tests.

European tree agreement vs. Black-Scholes, American >= European,
convergence with step count, and early-exercise-premium properties
from the PRD / master plan Task 03.
"""

import numpy as np
import pytest

from volsurf.binomial import binomial_price
from volsurf.bsm import black_scholes

# Representative subset of the PRD §9.1 grid (plan-03 item 5): one ATM and
# one OTM for each side, spanning time (0.08 / 0.25 / 0.5 / 1.0y), vol
# (0.1-0.4), and dividend (0-2%). The full spot × moneyness × maturity ×
# volatility cross-product is what the Greeks finite-difference test exercises.
GRID = [
    (100, 100, 1.0, 0.2, 0.05, 0.02),
    (100, 110, 0.25, 0.4, 0.03, 0.0),
    (90, 100, 0.08, 0.1, 0.05, 0.02),
    (100, 80, 0.5, 0.2, 0.05, 0.02),
]


class TestEuropeanAgreement:
    @pytest.mark.parametrize("S,K,T,sigma,r,q", GRID)
    @pytest.mark.parametrize("option", ["call", "put"])
    def test_matches_bsm_within_tol(self, S, K, T, sigma, r, q, option):
        tree = binomial_price(S, K, T, sigma, r, q, option, steps=500, american=False)
        bs = black_scholes(S, K, T, sigma, r, q, option)
        assert abs(tree - bs) < 0.01


class TestAmericanPremium:
    @pytest.mark.parametrize("S,K,T,sigma,r,q", GRID)
    @pytest.mark.parametrize("option", ["call", "put"])
    def test_american_ge_european(self, S, K, T, sigma, r, q, option):
        american = binomial_price(S, K, T, sigma, r, q, option, steps=1000, american=True)
        european = binomial_price(S, K, T, sigma, r, q, option, steps=1000, american=False)
        assert american >= european - 1e-10

    @pytest.mark.parametrize(
        "S,T,sigma,r",
        [(100, 0.25, 0.2, 0.05), (100, 1.0, 0.3, 0.1), (50, 0.08, 0.1, 0.03)],
    )
    def test_call_premium_zero_when_no_dividend(self, S, T, sigma, r):
        # q = 0: an American call on a non-dividend stock has no early-exercise premium
        for K in (S * 0.9, S, S * 1.1):
            american = binomial_price(S, K, T, sigma, r, 0.0, "call", steps=1000, american=True)
            european = binomial_price(S, K, T, sigma, r, 0.0, "call", steps=1000, american=False)
            assert american - european < 1e-6

    def test_put_premium_increases_with_rate(self):
        K, T, sigma, q = 100, 1.0, 0.2, 0.02
        prem_low = self._put_premium(K, T, sigma, 0.03, q)
        prem_high = self._put_premium(K, T, sigma, 0.06, q)
        assert prem_high >= prem_low

    @staticmethod
    def _put_premium(K, T, sigma, r, q):
        american = binomial_price(100, K, T, sigma, r, q, "put", steps=1000, american=True)
        european = binomial_price(100, K, T, sigma, r, q, "put", steps=1000, american=False)
        return american - european


class TestConvergence:
    def test_american_1000_steps_close_to_reference(self):
        # Reference computed at 10,000 steps; CRR oscillates, so also
        # check the average of consecutive step counts is small.
        S, K, T, sigma, r, q = 100, 100, 0.5, 0.3, 0.05, 0.02
        ref = binomial_price(S, K, T, sigma, r, q, "call", steps=10_000, american=True)
        err1000 = abs(binomial_price(S, K, T, sigma, r, q, "call", steps=1000, american=True) - ref)
        assert err1000 < 0.005

        avg = 0.5 * (
            binomial_price(S, K, T, sigma, r, q, "call", steps=999, american=True)
            + binomial_price(S, K, T, sigma, r, q, "call", steps=1000, american=True)
        )
        assert abs(avg - ref) < 0.002


class TestValidityBoundary:
    def test_raises_when_probability_out_of_range(self):
        # At tiny step counts, sigma so small that e^((r-q)dt) > u -> p > 1
        with pytest.raises(ValueError):
            binomial_price(100, 100, 1 / 365, 1e-4, 0.05, 0.02, "call", steps=10, american=True)


class TestAtTheMoneySmoke:
    def test_price_dimensions(self):

        spots = np.array([90.0, 100.0, 110.0])
        out = [
            binomial_price(s, 100, 0.25, 0.2, 0.05, 0.0, "call", steps=200, american=True)
            for s in spots
        ]
        assert len(out) == 3
        assert all(np.isfinite(out))


class TestDeterministicBoundaries:
    @pytest.mark.parametrize("option", ["call", "put"])
    def test_zero_maturity_returns_intrinsic(self, option):
        S, K = (110, 100) if option == "call" else (90, 100)
        price = binomial_price(S, K, 0.0, 0.2, 0.05, 0.02, option, steps=10, american=True)
        assert price == pytest.approx(10.0)

    def test_zero_volatility_has_clear_error(self):
        with pytest.raises(ValueError, match="zero volatility"):
            binomial_price(110, 100, 1.0, 0.0, 0.05, 0.02, "call")

    def test_european_large_step_count_is_finite_and_converges(self):
        params = (100, 100, 0.5, 0.3, 0.05, 0.02, "call")
        tree = binomial_price(*params, steps=10_000, american=False)
        bs = black_scholes(*params)
        assert np.isfinite(tree)
        assert abs(tree - bs) < 0.01
