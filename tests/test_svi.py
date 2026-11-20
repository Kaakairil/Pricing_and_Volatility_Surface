"""SVI slice fit + butterfly check (Task 11, stretch FR-10)."""

import numpy as np
import pandas as pd
import pytest

from volsurf.svi import (
    check_butterfly,
    fit_svi_slice,
    svi_total_variance,
)

# A known, butterfly-clean parameter set (Gatheral-style synthetic smile).
TRUE_PARAMS = {"a": 0.04, "b": 0.10, "rho": -0.30, "m": 0.00, "sigma": 0.20}


def svi_dict_to_vec(p):
    return np.array([p["a"], p["b"], p["rho"], p["m"], p["sigma"]])


def vec_to_svi_dict(v):
    return dict(zip(("a", "b", "rho", "m", "sigma"), map(float, v), strict=False))


class TestSviTotalVariance:
    def test_value_at_reference_points(self):
        k = np.array([-0.2, 0.0, 0.2])
        w = svi_total_variance(TRUE_PARAMS, k)
        svi_dict_to_vec(TRUE_PARAMS)  # not used numerically; shape guard
        assert w.shape == k.shape
        assert np.isfinite(w).all()
        # monotone right wing rises: w(0.2) > w(0) > w(-0.2) for rho<0? Only
        # left wing is steeper for rho<0 — check w(0) equals closed form.
        km = 0.0
        closed = TRUE_PARAMS["a"] + TRUE_PARAMS["b"] * (
            TRUE_PARAMS["rho"] * (km - TRUE_PARAMS["m"])
            + np.sqrt((km - TRUE_PARAMS["m"]) ** 2 + TRUE_PARAMS["sigma"] ** 2)
        )
        assert w[1] == pytest.approx(closed, rel=1e-12)

    def test_vectorized_matches_scalar(self):
        k = np.linspace(-0.5, 0.5, 21)
        w = svi_total_variance(TRUE_PARAMS, k)
        for ki, wi in zip(k, w, strict=False):
            assert wi == pytest.approx(svi_total_variance(TRUE_PARAMS, np.array([ki]))[0])


class TestFitSlice:
    def _synthetic_slice(self, params, k, noise=0.0, seed=7):
        rng = np.random.default_rng(seed)
        w = svi_total_variance(params, k)
        w = w * (1 + noise * rng.standard_normal(len(k)))
        return k, np.maximum(w, 1e-10)

    def test_recovers_known_params(self):
        k = np.linspace(-0.4, 0.4, 21)
        k, w = self._synthetic_slice(TRUE_PARAMS, k)
        params = fit_svi_slice(k, w)
        got = svi_dict_to_vec(params)
        want = svi_dict_to_vec(TRUE_PARAMS)
        assert np.allclose(got, want, atol=1e-3), f"{params} vs {TRUE_PARAMS}"

    def test_fit_minimizes_residuals_vs_perturbed_start(self):
        # A poor x0 still converges to (close to) the same optimum.
        k = np.linspace(-0.4, 0.4, 21)
        k, w = self._synthetic_slice(TRUE_PARAMS, k)
        p1 = fit_svi_slice(k, w)
        p2 = fit_svi_slice(k, w, x0={"a": 0.5, "b": 0.2, "rho": 0.5, "m": -0.3, "sigma": 0.9})
        w1 = svi_total_variance(p1, k)
        w2 = svi_total_variance(p2, k)
        assert np.sqrt(np.mean((w1 - w2) ** 2)) < 1e-6

    def test_constraint_violation_rejected(self):
        # b < 0 is outside the admissible set; the fit must not return it.
        k = np.linspace(-0.3, 0.3, 15)
        clean = {"a": 0.02, "b": 0.08, "rho": -0.2, "m": 0.0, "sigma": 0.15}
        _, w = self._synthetic_slice(clean, k)
        params = fit_svi_slice(k, w)
        assert params["b"] >= 0.0
        assert abs(params["rho"]) < 1.0
        assert params["sigma"] > 0.0
        assert (
            params["a"] + params["b"] * params["sigma"] * np.sqrt(1 - params["rho"] ** 2) >= -1e-12
        )

    def test_requires_matching_lengths(self):
        with pytest.raises(ValueError, match="length"):
            fit_svi_slice(np.array([0.0, 0.1]), np.array([0.04]))
        with pytest.raises(ValueError, match="finite"):
            fit_svi_slice(
                np.array([0.0, 0.1, 0.2, 0.3, 0.4, np.nan]),
                np.array([0.04, 0.05, 0.06, 0.07, 0.08, 0.09]),
            )


class TestButterfly:
    def test_clean_slice_passes(self):
        k = np.linspace(-1.0, 1.0, 401)
        params = fit_svi_slice(k, svi_total_variance(TRUE_PARAMS, k))
        ok, min_g = check_butterfly(params, k)
        assert ok and min_g > -1e-6

    def test_engineered_violation_flagged(self):
        # The right-wing slope s = b(1+rho) ~ 3: the asymptotic
        # g -> 1 - s + 3s^2/16 is negative for wing slope in (4/3, 4).
        bad = {"a": 0.1, "b": 2.0, "rho": 0.5, "m": 0.0, "sigma": 0.1}
        k = np.linspace(-1.0, 1.0, 401)
        ok, min_g = check_butterfly(bad, k)
        assert not ok and min_g < 0


class TestOnSnapshotData:
    """Integration: fit real cleaned expiries from the committed results."""

    @pytest.fixture(scope="class")
    def fits(self):
        from volsurf.svi import fit_snapshot_slices

        table = pd.read_csv(
            "D:/Kuliah/Hackathon/Options pricing and volatility surface/results/iv_table.csv"
        )
        ok = table[(table.reason == "ok") & table.american.notna()]
        return fit_snapshot_slices(ok, n_slices=3)

    def test_three_slices_fitted(self, fits):
        assert len(fits) == 3

    def test_fits_constraints_and_rmse(self, fits):
        for f in fits:
            p = f["params"]
            assert p["b"] >= 0 and abs(p["rho"]) < 1 and p["sigma"] > 0
            assert f["rmse_in_iv"] < 0.05

    def test_fit_csv_written(self, fits, tmp_path):
        from volsurf.svi import write_svi_fit_csv

        out = write_svi_fit_csv(fits, tmp_path)
        assert out.exists()
        read = pd.read_csv(out)
        assert len(read) == 3
        assert set(read.columns).issuperset({"tte", "a", "b", "rho", "m", "sigma", "rmse_in_iv"})
