"""Monte Carlo GBM tests.

Task 04: black_scholes within 3 SE across a grid, seed-to-seed spread
consistent with the reported SE, and the control variate reducing the
standard error of the raw point estimator.
"""

import numpy as np
import pytest

from volsurf.bsm import black_scholes
from volsurf.montecarlo import monte_carlo_price

GRID = [
    (100, 100, 1.0, 0.2, 0.05, 0.02),
    (100, 110, 0.25, 0.4, 0.03, 0.0),
    (90, 100, 0.08, 0.1, 0.05, 0.02),
    (100, 80, 0.5, 0.2, 0.05, 0.02),
]


class TestAgreementWithBlackScholes:
    @pytest.mark.parametrize("S,K,T,sigma,r,q", GRID)
    @pytest.mark.parametrize("option", ["call", "put"])
    def test_within_3_se(self, S, K, T, sigma, r, q, option):
        price, se = monte_carlo_price(S, K, T, sigma, r, q, option, paths=200_000)
        bs = black_scholes(S, K, T, sigma, r, q, option)
        assert abs(price - bs) < 3 * se


class TestSeedSpread:
    def test_estimates_consistent_with_reported_se(self):
        prices, ses = [], []
        for seed in range(30):
            price, se = monte_carlo_price(
                100, 100, 0.5, 0.3, 0.05, 0.02, "call", paths=50_000, seed=seed
            )
            prices.append(price)
            ses.append(se)
        ratio = float(np.std(prices) / np.mean(ses))
        assert 0.8 <= ratio <= 1.25


class TestControlVariate:
    def test_control_reduces_standard_error(self):
        raw_price, raw_se = monte_carlo_price(
            100, 100, 0.5, 0.3, 0.05, 0.02, "call", paths=100_000, control=False
        )
        adj_price, adj_se = monte_carlo_price(
            100, 100, 0.5, 0.3, 0.05, 0.02, "call", paths=100_000, control=True
        )
        assert np.isfinite(raw_price) and np.isfinite(adj_price)
        assert adj_se < raw_se


class TestInputValidation:
    def test_rejects_bad_option(self):
        with pytest.raises(ValueError):
            monte_carlo_price(100, 100, 0.5, 0.2, 0.05, 0.02, "straddle", paths=10)

    def test_rejects_nonpositive_paths(self):
        with pytest.raises(ValueError):
            monte_carlo_price(100, 100, 0.5, 0.2, 0.05, 0.02, "call", paths=0)


class TestMonteCarloEdgeCases:
    def test_zero_maturity_degenerate_control_returns_finite_price_and_zero_se(self):
        price, se = monte_carlo_price(110, 100, 0.0, 0.2, 0.05, 0.02, "call", paths=100)
        assert np.isfinite(price)
        assert se == 0.0

    @pytest.mark.parametrize("paths", [0, 1])
    def test_requires_at_least_two_paths(self, paths):
        with pytest.raises(ValueError, match="paths"):
            monte_carlo_price(100, 100, 0.5, 0.2, 0.05, 0.02, "call", paths=paths)

    def test_rejects_odd_antithetic_path_count(self):
        with pytest.raises(ValueError, match="even"):
            monte_carlo_price(100, 100, 0.5, 0.2, 0.05, 0.02, "call", paths=5)

    def test_rejects_nonfinite_spot(self):
        with pytest.raises(ValueError):
            monte_carlo_price(float("nan"), 100, 0.5, 0.2, 0.05, 0.02, "call", paths=100)


class TestBinomialCrossCheck:
    def test_european_binomial_agrees_with_monte_carlo(self):
        from volsurf.binomial import binomial_price

        params = (100, 105, 0.5, 0.25, 0.04, 0.015, "put")
        mc, se = monte_carlo_price(*params, paths=200_000, seed=17)
        tree = binomial_price(*params, steps=1_000, american=False)
        assert abs(tree - mc) <= 0.01 + 3 * se
