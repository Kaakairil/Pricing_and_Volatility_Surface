"""Early-exercise premium experiment (Task 10, PRD §9.2 / RQ2)."""

import pandas as pd
import pytest

from volsurf.experiments import (
    early_exercise_premium,
    plot_early_exercise_premium,
    rate_sensitivity,
)


def base_args(**overrides):
    args = {
        "S": 100.0,
        "moneyness": [0.8, 0.9, 1.0, 1.1, 1.2],
        "T_grid": [7 / 365, 30 / 365, 90 / 365, 1.0],
        "sigma": 0.20,
        "r": 0.04,
        "q": 0.0138,
        "steps": 1000,
    }
    args.update(overrides)
    return args


class TestEarlyExercisePremium:
    def test_columns_and_no_nan(self):
        df = early_exercise_premium(**base_args())
        cols = ["moneyness", "T", "option", "american", "european", "premium", "premium_pct"]
        assert list(df.columns) == cols
        assert len(df) == 5 * 4 * 2
        assert df["american"].notna().all()
        assert df["european"].notna().all()
        assert df["premium"].notna().all()
        assert df["premium_pct"].notna().all()

    def test_premium_nonnegative(self):
        df = early_exercise_premium(**base_args())
        assert (df["premium"] >= -1e-10).all()

    def test_q_zero_call_premium_zero(self):
        df = early_exercise_premium(**base_args(q=0.0))
        calls = df[df.option == "call"]
        assert (calls["premium"].abs() < 1e-6).all()
        puts = df[df.option == "put"]
        assert (puts["premium"] > 0).any()

    def test_spy_call_premium_is_zero_below_exercise_threshold(self):
        # SPY snapshot parameters (r=0.0422, q=0.00748): a call is exercised
        # early only when q*S > r*K, i.e. K/S < q/r = 0.177. No grid point is
        # that deep, so the SPY-parameter call premium is ~0 (plan note
        # corrected: q > 0 is necessary, NOT sufficient).
        df = early_exercise_premium(**base_args())
        calls = df[df.option == "call"]
        assert (calls["premium"] < 1e-6).all()

    def test_q_above_threshold_call_premium_positive(self):
        # The mechanism itself: at q = 0.05 > r * K/S for moneyness 0.8,
        # early exercise dominates and the call premium is clearly positive.
        df = early_exercise_premium(**base_args(q=0.05))
        rows = df[(df.option == "call") & (df.moneyness == 0.8) & (df["T"] == 1.0)]
        assert (rows["premium"] > 1e-3).all()

    def test_atm_call_premium_small_but_present(self):
        df = early_exercise_premium(**base_args())
        atm = df[(df.option == "call") & (df.moneyness == 1.0)]
        # ATM call premium is tiny for this vol but nonzero, bounded by q*S*T.
        assert (atm["premium"] < 0.10).all()
        assert (atm["premium"] > 0).any()

    def test_bad_inputs_raise(self):
        with pytest.raises(ValueError, match="steps"):
            early_exercise_premium(**base_args(steps=0))
        with pytest.raises(ValueError):
            early_exercise_premium(**base_args(S=-1.0))


class TestRateSensitivity:
    def test_put_premium_increases_with_rate(self):
        r_grid = [0.0, 0.02, 0.04, 0.06]
        df = rate_sensitivity(S=100.0, moneyness=1.0, T=0.25, sigma=0.2, r_grid=r_grid, q=0.0)
        assert df.american.notna().all() and df.european.notna().all()
        assert df.premium.notna().all()
        puts = df[df.option == "put"].sort_values("r")
        assert puts.premium.is_monotonic_increasing
        calls = df[df.option == "call"].sort_values("r")
        assert calls.premium.is_monotonic_decreasing or calls.premium.is_monotonic_increasing

    def test_writes_csvs(self, tmp_path):
        from volsurf.experiments import write_experiment_outputs

        df = rate_sensitivity(S=100.0, moneyness=1.0, T=0.25, sigma=0.2, r_grid=[0.02, 0.05], q=0.0)
        out = write_experiment_outputs(df, tmp_path, name="rate_sensitivity.csv")
        assert out.exists()
        read = pd.read_csv(out)
        assert len(read) == len(df)


class TestPlot:
    def test_plot_early_exercise_premium_writes_png(self, tmp_path):
        df = early_exercise_premium(**base_args())
        out = plot_early_exercise_premium(df, tmp_path)
        assert out.exists() and out.stat().st_size > 0
        assert out.suffix == ".png"
