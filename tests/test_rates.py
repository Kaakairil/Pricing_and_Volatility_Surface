"""Rate and dividend-yield conversion tests (Task 06)."""

import math

import pytest

from volsurf.rates import dividend_yield_continuous, risk_free_from_dtb3


class TestRiskFreeFromDtb3:
    def test_hand_value_91_day(self):
        # P = 1 - 0.05*91/360; r = -ln(P)*365/91
        price = 1.0 - 0.05 * 91 / 360.0
        expected = -math.log(price) * 365.0 / 91.0
        assert risk_free_from_dtb3(0.05) == pytest.approx(expected)

    def test_zero_discount_yields_zero(self):
        assert risk_free_from_dtb3(0.0) == pytest.approx(0.0)

    def test_tenor_changes_rate(self):
        # Longer tenor at the same discount rate -> higher continuous rate
        # (the discount is spread differently under 365-day compounding).
        assert risk_free_from_dtb3(0.04, 182) != pytest.approx(risk_free_from_dtb3(0.04, 91))

    @pytest.mark.parametrize("bad", [float("nan"), float("inf"), -0.01, 2.0])
    def test_rejects_invalid_discount(self, bad):
        with pytest.raises(ValueError):
            risk_free_from_dtb3(bad)

    def test_rejects_nonpositive_tenor(self):
        with pytest.raises(ValueError):
            risk_free_from_dtb3(0.05, tenor_days=0)


class TestDividendYieldContinuous:
    def test_hand_value(self):
        # discrete yield 1.0/20.0 = 5%; q = ln(1.05)
        assert dividend_yield_continuous(1.0, 20.0) == pytest.approx(math.log(1.05))

    def test_zero_dividends(self):
        assert dividend_yield_continuous(0.0, 100.0) == pytest.approx(0.0)

    def test_increases_with_dividends(self):
        q_low = dividend_yield_continuous(1.0, 100.0)
        q_high = dividend_yield_continuous(2.0, 100.0)
        assert q_high > q_low

    @pytest.mark.parametrize("bad", [float("nan"), float("inf"), -1.0])
    def test_rejects_invalid_trailing(self, bad):
        with pytest.raises(ValueError):
            dividend_yield_continuous(bad, 100.0)

    @pytest.mark.parametrize("bad", [0.0, -5.0, float("nan")])
    def test_rejects_invalid_spot(self, bad):
        with pytest.raises(ValueError):
            dividend_yield_continuous(1.0, bad)
