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
        for seed in range(10):
            price, se = monte_carlo_price(
                100, 100, 0.5, 0.3, 0.05, 0.02, "call", paths=50_000, seed=seed
            )
            prices.append(price)
            ses.append(se)
        ratio = float(np.std(prices) / np.mean(ses))
        assert 0.7 <= ratio <= 1.3


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
