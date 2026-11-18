"""IV table, surface interpolation, calendar diagnostic (Task 09)."""

import numpy as np
import pandas as pd
import pytest

from volsurf.binomial import binomial_price
from volsurf.market_data import save_snapshot


def table(rows, **overrides):
    from volsurf.surface import compute_iv_table

    args = {"spot": 100.0, "r": 0.0, "q": 0.0, **overrides}
    return compute_iv_table(pd.DataFrame(rows), **args)


def build_surface(*args, **kwargs):
    from volsurf.surface import build_surface

    return build_surface(*args, **kwargs)


class TestComputeIVTable:
    def test_american_reason_codes_and_columns(self):
        rows = [
            {"strike": 100.0, "tte": 0.25, "mid": 8.0, "option": "call"},
            {"strike": 10.0, "tte": 0.25, "mid": 75.0, "option": "call"},
            {"strike": 200.0, "tte": 0.25, "mid": 93.0, "option": "call"},
        ]
        out = table(rows)
        cols = ["strike", "tte", "option", "mid", "k", "iv", "reason"]
        assert list(out.columns) == cols
        reasons = out.set_index("strike").reason
        assert reasons[100.0] == "ok"
        assert reasons[10.0] == "LOW-NA"
        assert reasons[200.0] == "NO-BRACKET"
        assert out["iv"].notna().sum() == 1
        assert out.iv[out.strike == 100.0].iloc[0] == pytest.approx(0.402, abs=1e-3)

    def test_european_bs_comparison_column(self):
        rows = [
            {"strike": 100.0, "tte": 0.25, "mid": 8.0, "option": "call"},
            {"strike": 105.0, "tte": 0.25, "mid": 6.0, "option": "put"},
        ]
        out = table(rows, style="european")
        assert out.iv.notna().all() and out.reason.eq("ok").all()
        assert (out.iv > 0).all()

    def test_american_crr_difference_from_european(self):
        T, r, q = 0.25, 0.05, 0.02
        rows = [
            {
                "strike": K,
                "tte": T,
                "mid": binomial_price(100, K, T, 0.35, r, q, side, steps=300, american=True),
                "option": side,
            }
            for K, side in ((100, "call"), (100, "put"))
        ]
        am = table(rows, r=r, q=q, style="american", steps=300)
        eu = table(rows, r=r, q=q, style="european")
        assert am.reason.eq("ok").all()
        assert eu.reason.eq("ok").all()
        assert (am.iv - eu.iv).abs().max() > 1e-6

    def test_requires_mid_columns_positive_spot(self):
        with pytest.raises(ValueError, match="missing"):
            table([{"strike": 100.0, "tte": 0.25, "option": "call"}])
        with pytest.raises(ValueError):
            table([{"strike": 100.0, "tte": 0.25, "mid": 8.0, "option": "call"}], spot=-1.0)
        with pytest.raises(ValueError):
            table([{"strike": 100.0, "tte": float("nan"), "mid": 8.0, "option": "call"}])

    def test_bad_style_and_bad_steps_raise(self):
        row = {"strike": 100.0, "tte": 0.25, "mid": 8.0, "option": "call"}
        with pytest.raises(ValueError, match="style"):
            table([row], style="bogus")
        with pytest.raises(ValueError):
            table([row], steps=0)


class TestBuildSurface:
    def _iv_df(self):
        k = np.linspace(-0.4, 0.4, 9)
        T = np.array([0.25, 0.5, 1.0])
        rows = [{"k": kk, "tte": tt, "iv": 0.2 + 0.1 * kk + 0.05 * tt} for tt in T for kk in k]
        return pd.DataFrame(rows)

    def test_reproduces_input_ivs_at_nodes_within_1e8(self):
        df = self._iv_df()
        grid, method = build_surface(df)
        # The interpolant reproduces input IVs exactly at their (k, tte) nodes;
        # the coarse grid lattice need not include them, so query the interpolator.
        for _, row in df.iterrows():
            got = float(method["interpolator"](row.k, row.tte))
            assert abs(got - row.iv) < 1e-8
        assert method["method"] == "LinearNDInterpolator"

    def test_nan_iv_points_dropped_and_count_logged(self):
        df = self._iv_df()
        df.loc[2, "iv"] = np.nan
        df.loc[5, "iv"] = np.nan
        grid, method = build_surface(df)
        assert method["dropped_nan"] == 2
        assert method["input_rows"] == len(self._iv_df())
        assert grid.iv.notna().any()

    def test_missing_inputs_error(self):
        with pytest.raises(ValueError, match="missing"):
            build_surface(pd.DataFrame({"k": [0.0], "tte": [0.3]}))
        with pytest.raises(ValueError, match="4 finite IV points"):
            build_surface(pd.DataFrame({"k": [0.0], "tte": [0.3], "iv": [0.2]}))

    def test_out_of_hull_grid_is_nan_never_extrapolated(self):
        df = self._iv_df()
        grid, method = build_surface(df)
        for k in (3.0, -3.0):
            assert np.isnan(method["interpolator"](k, 0.25))
        # grid points far outside the hull carry NaN, never a silent fill
        assert grid.iv.isna().any()

    def test_matches_snapshot_columns(self):
        df = self._iv_df()
        grid, method = build_surface(df)
        assert method["col_count"] == len(df)
        assert method["n_points"] == len(df)
        assert method["k_min"] == pytest.approx(-0.4)
        assert method["k_max"] == pytest.approx(0.4)
        assert "empty" not in method


class TestCalendarDiagnostic:
    def _times(self):
        return [0.25, 0.5, 1.0]

    def test_normal_term_structure_has_no_warnings(self):
        from volsurf.surface import calendar_diagnostic

        T = self._times()
        rows = []
        for tte in T:
            for kk in (-0.1, 0.0, 0.1):
                rows.append({"k": kk, "tte": tte, "iv": 0.2 + 0.6 * tte})
        diag = calendar_diagnostic(pd.DataFrame(rows))
        assert diag.total_var_decrease.eq(False).all()
        assert diag.warning.eq(False).all()
        assert set(diag.columns) == {"k", "tte_pair", "total_var_decrease", "warning"}

    def test_decreasing_total_variance_warns(self):
        from volsurf.surface import calendar_diagnostic

        rows = [{"k": 0.0, "tte": 0.25, "iv": 0.5}, {"k": 0.0, "tte": 0.5, "iv": 0.2}]
        diag = calendar_diagnostic(pd.DataFrame(rows))
        assert diag.total_var_decrease.eq(True).all()
        assert diag.warning.eq(True).all()


class TestCLIRegresses:
    def test_surface_cli_write_iv_table_and_figures(self, tmp_path):
        from volsurf.cli import main

        rows = [
            {
                "strike": K,
                "bid": b,
                "ask": b + 0.4,
                "option": "call",
                "expiry": exp,
                "openInterest": 1000,
                "volume": 10,
            }
            for exp, Kb in (
                ("2027-03-19", ((95, 12.0), (100, 8.0), (105, 4.5), (110, 2.0))),
                ("2027-06-18", ((95, 13.0), (100, 9.5), (105, 6.5), (110, 4.5))),
            )
            for K, b in Kb
        ]
        rows += [
            {
                "strike": K,
                "bid": b,
                "ask": b + 0.5,
                "option": "put",
                "expiry": "2027-03-19",
                "openInterest": 1000,
                "volume": 10,
            }
            for K, b in ((95, 2.0), (100, 4.0), (105, 7.0), (110, 11.0))
        ]
        meta = {"snapshot_date": "2026-11-16", "spot": 100.0}
        snap = save_snapshot(pd.DataFrame(rows), meta, tmp_path)
        out = tmp_path / "out"
        assert main(["surface", str(snap), "-o", str(out)]) == 0

        table_csv = out / "iv_table.csv"
        assert table_csv.exists()
        data = pd.read_csv(table_csv)
        assert set(data.columns).issuperset({"iv", "reason", "k"})
        assert "american" in data.columns and "european" in data.columns
        assert data.reason.eq("ok").all()
        assert (data.american.notna()).all() and (data.european.notna()).all()
        assert len(data) == 12

        fig = out / "surface" / "smile_2027-03-19.png"
        assert fig.exists() and fig.stat().st_size > 0

    def test_surface_cli_runs_on_missing_rate_key(self, tmp_path):
        from volsurf.cli import main

        rows = [
            {
                "strike": K,
                "bid": b,
                "ask": b + 0.4,
                "option": "call",
                "expiry": exp,
                "openInterest": 1000,
                "volume": 10,
            }
            for exp, Kb in (
                ("2027-03-19", ((95, 12.0), (100, 8.0), (105, 4.5), (110, 2.0))),
                ("2027-06-18", ((95, 13.0), (100, 9.5), (105, 6.5), (110, 4.5))),
            )
            for K, b in Kb
        ]
        snap = save_snapshot(
            pd.DataFrame(rows), {"snapshot_date": "2026-11-16", "spot": 100.0}, tmp_path
        )
        out = tmp_path / "out"
        assert main(["surface", str(snap), "-o", str(out)]) == 0
        assert (out / "iv_table.csv").exists()
        assert (out / "surface_method.csv").exists()
