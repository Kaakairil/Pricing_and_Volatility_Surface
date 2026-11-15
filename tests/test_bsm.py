"""BSM pricing tests. Benchmarks from Hull, *Options, Futures, and Other
Derivatives* (11th ed.), Ch. 15 worked examples."""

import math

import pytest

from volsurf.bsm import black_scholes


class TestBenchmarks:
    def test_hull_call_example(self):
        # Hull 11th ed: S=42, K=40, r=0.10, sigma=0.20, T=0.5, q=0 -> call = 4.76
        assert abs(black_scholes(42, 40, 0.5, 0.20, 0.10, 0.0, "call") - 4.76) < 0.01

    def test_hull_put_example(self):
        # Same params -> put = 0.81
        assert abs(black_scholes(42, 40, 0.5, 0.20, 0.10, 0.0, "put") - 0.81) < 0.01


class TestPutCallParity:
    @pytest.mark.parametrize(
        "S,K,T,sigma,r,q",
        [
            (100, 100, 1.0, 0.2, 0.05, 0.02),
            (100, 110, 0.25, 0.4, 0.03, 0.0),
            (90, 100, 0.08, 0.1, 0.05, 0.02),
        ],
    )
    def test_parity_machine_precision(self, S, K, T, sigma, r, q):
        C = black_scholes(S, K, T, sigma, r, q, "call")
        P = black_scholes(S, K, T, sigma, r, q, "put")
        lhs = C - P
        rhs = S * math.exp(-q * T) - K * math.exp(-r * T)
        assert abs(lhs - rhs) < 1e-10


class TestMonotonicity:
    def test_call_decreasing_in_strike(self):
        prices = [
            black_scholes(100, K, 0.25, 0.2, 0.05, 0.02, "call") for K in (90, 95, 100, 105, 110)
        ]
        assert all(a > b for a, b in zip(prices, prices[1:], strict=False))

    def test_call_increasing_in_sigma(self):
        prices = [black_scholes(100, 100, 0.25, s, 0.05, 0.02, "call") for s in (0.1, 0.2, 0.4)]
        assert all(a < b for a, b in zip(prices, prices[1:], strict=False))

    def test_call_increasing_in_maturity_no_dividends(self):
        prices = [black_scholes(100, 100, T, 0.2, 0.05, 0.0, "call") for T in (0.08, 0.25, 1.0)]
        assert all(a < b for a, b in zip(prices, prices[1:], strict=False))


class TestEdgeCases:
    def test_zero_maturity_returns_intrinsic_call(self):
        S, K = 110, 100
        assert black_scholes(S, K, 0.0, 0.2, 0.05, 0.02, "call") == pytest.approx(S - K, abs=1e-12)

    def test_zero_maturity_returns_intrinsic_put(self):
        S, K = 90, 100
        assert black_scholes(S, K, 0.0, 0.2, 0.05, 0.02, "put") == pytest.approx(K - S, abs=1e-12)

    def test_zero_vol_returns_discounted_intrinsic(self):
        # sigma=0: deterministic terminal; call worth max(S e^{-qT} - K e^{-rT}, 0)
        S, K, T, r, q = 100, 95, 1.0, 0.05, 0.02
        expected = max(S * math.exp(-q * T) - K * math.exp(-r * T), 0.0)
        assert black_scholes(S, K, T, 0.0, r, q, "call") == pytest.approx(expected, abs=1e-10)

    def test_bad_option_type_raises(self):
        with pytest.raises(ValueError):
            black_scholes(100, 100, 1.0, 0.2, 0.05, 0.02, "straddle")

    def test_bad_inputs_raise(self):
        with pytest.raises(ValueError):
            black_scholes(-100, 100, 1.0, 0.2, 0.05, 0.02, "call")
        with pytest.raises(ValueError):
            black_scholes(100, 0, 1.0, 0.2, 0.05, 0.02, "call")
        with pytest.raises(ValueError):
            black_scholes(100, 100, -1.0, 0.2, 0.05, 0.02, "call")
        with pytest.raises(ValueError):
            black_scholes(100, 100, 1.0, -0.2, 0.05, 0.02, "call")


class TestGreeksEdgeCases:
    def test_greeks_at_zero_maturity(self):
        from volsurf.bsm import delta, gamma, rho, theta, vega

        assert delta(110, 100, 0.0, 0.2, 0.05, 0.02, "call") == pytest.approx(1.0)
        assert delta(90, 100, 0.0, 0.2, 0.05, 0.02, "call") == pytest.approx(0.0)
        assert delta(90, 100, 0.0, 0.2, 0.05, 0.02, "put") == pytest.approx(-1.0)
        assert delta(110, 100, 0.0, 0.2, 0.05, 0.02, "put") == pytest.approx(0.0)
        assert gamma(100, 100, 0.0, 0.2, 0.05, 0.02, "call") == 0.0
        assert vega(100, 100, 0.0, 0.2, 0.05, 0.02, "call") == 0.0
        assert theta(100, 100, 0.0, 0.2, 0.05, 0.02, "call") == 0.0
        assert rho(110, 100, 0.0, 0.2, 0.05, 0.02, "call") == 0.0
        assert rho(90, 100, 0.0, 0.2, 0.05, 0.02, "put") == 0.0

    def test_greeks_at_zero_vol(self):
        from volsurf.bsm import delta, gamma, rho, theta, vega

        # ITM call & ITM put with positive T, sigma=0: deterministic limit matches FD
        assert gamma(110, 100, 1.0, 0.0, 0.05, 0.02, "call") == 0.0
        assert vega(110, 100, 1.0, 0.0, 0.05, 0.02, "call") == 0.0
        assert delta(110, 100, 1.0, 0.0, 0.05, 0.02, "call") == pytest.approx(math.exp(-0.02))
        assert delta(90, 100, 1.0, 0.0, 0.05, 0.02, "put") == pytest.approx(-math.exp(-0.02))
        assert theta(110, 100, 1.0, 0.0, 0.05, 0.02, "call") != 0.0
        assert theta(90, 100, 1.0, 0.0, 0.05, 0.02, "call") == 0.0
        assert theta(90, 100, 1.0, 0.0, 0.05, 0.02, "put") != 0.0
        assert theta(110, 100, 1.0, 0.0, 0.05, 0.02, "put") == 0.0
        assert rho(110, 100, 1.0, 0.0, 0.05, 0.02, "call") > 0.0
        assert rho(90, 100, 1.0, 0.0, 0.05, 0.02, "call") == 0.0
        assert rho(90, 100, 1.0, 0.0, 0.05, 0.02, "put") < 0.0
        assert rho(110, 100, 1.0, 0.0, 0.05, 0.02, "put") == 0.0
