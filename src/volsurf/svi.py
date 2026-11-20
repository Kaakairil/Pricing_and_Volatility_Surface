"""SVI slice fit (Task 11, stretch FR-10).

Raw SVI total-variance parameterization (Gatheral 2004):

    w(k) = a + b * (rho * (k - m) + sqrt((k - m)^2 + sigma^2))

Fitted per expiry on total variance w = IV^2 * T with
``scipy.optimize.least_squares`` and hard bounds enforcing b >= 0,
|rho| < 1, sigma > 0 during the fit; the a + b*sigma*sqrt(1 - rho^2) >= 0
convexity-side condition is checked after each fit (all but one bound-set is
re-scanned from many starts, so a violating optimum is discarded, not
returned). Butterfly arbitrage is screened with the Gatheral (2014) density
condition g(k) >= 0 on a dense grid.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import least_squares

# Raw-parameter bounds: (a, b, rho, m, sigma)
BOUNDS_LO = np.array([-np.inf, 0.0, -0.999, -np.inf, 1e-6])
BOUNDS_HI = np.array([np.inf, np.inf, 0.999, np.inf, np.inf])

# Deterministic multi-start grid (a, b, rho, m, sigma) to escape local minima.
_STARTS = (
    (0.01, 0.1, -0.3, 0.0, 0.2),
    (0.04, 0.2, -0.5, 0.0, 0.3),
    (0.0, 0.05, 0.0, 0.1, 0.1),
    (0.02, 0.4, -0.7, -0.1, 0.5),
)

PARAM_NAMES = ("a", "b", "rho", "m", "sigma")


def svi_total_variance(params: dict, k: np.ndarray | float) -> np.ndarray:
    """SVI total variance w(k) = a + b(rho(k-m) + sqrt((k-m)^2 + sigma^2))."""
    a, b, rho, m, sigma = (params[name] for name in PARAM_NAMES)
    k = np.asarray(k, dtype=float)
    km = k - m
    return a + b * (rho * km + np.sqrt(km * km + sigma * sigma))


def _w_residuals(x: np.ndarray, k: np.ndarray, w: np.ndarray, weights) -> np.ndarray:
    params = dict(zip(PARAM_NAMES, x, strict=False))
    model = svi_total_variance(params, k)
    res = model - w
    if weights is not None:
        res = res * weights
    return res


def _admissible(params: dict) -> bool:
    """Full admissibility: bounds plus a + b*sigma*sqrt(1 - rho^2) >= 0."""
    a, b, rho, m, sigma = (params[name] for name in PARAM_NAMES)
    if not (b >= 0.0 and abs(rho) < 1.0 and sigma > 0.0):
        return False
    return bool(a + b * sigma * np.sqrt(1.0 - rho * rho) >= -1e-12)


def fit_svi_slice(k, total_var, weights=None, x0=None) -> dict:
    """Fit one SVI slice on total variance; returns params {a, b, rho, m, sigma}.

    Enforces b >= 0, |rho| < 1, sigma > 0 via hard bounds during the fit;
    many deterministic starts scan for the global optimum, and any start whose
    optimum violates the a + b*sigma*sqrt(1-rho^2) >= 0 condition is discarded.
    Raises ValueError on non-finite or mismatched inputs.
    """
    k = np.asarray(k, dtype=float)
    w = np.asarray(total_var, dtype=float)
    if k.shape != w.shape:
        raise ValueError(f"k and total_var must have the same length, got {k.shape} vs {w.shape}")
    if len(k) < 5:
        raise ValueError(f"SVI fit needs >= 5 points, got {len(k)}")
    if not (np.isfinite(k).all() and np.isfinite(w).all()):
        raise ValueError("k and total_var must be finite")
    if (w <= 0).any():
        raise ValueError("total_var must be positive")

    starts = (
        [np.array([x0[name] for name in PARAM_NAMES], dtype=float)]
        if x0
        else [np.array(s, dtype=float) for s in _STARTS]
    )

    best = None
    best_cost = np.inf
    for x0v in starts:
        x0v = np.clip(x0v, BOUNDS_LO + 1e-9, BOUNDS_HI - 1e-9)
        try:
            res = least_squares(
                _w_residuals,
                x0v,
                args=(k, w, weights),
                bounds=(BOUNDS_LO, BOUNDS_HI),
                xtol=1e-12,
                ftol=1e-12,
                max_nfev=20000,
            )
        except Exception:
            continue
        params = dict(zip(PARAM_NAMES, res.x, strict=False))
        if not _admissible(params):
            continue
        if res.cost < best_cost:
            best_cost = res.cost
            best = params
    if best is None:
        raise ValueError("no admissible SVI fit found for this slice")
    return best


def check_butterfly(params: dict, k_grid) -> tuple[bool, float]:
    """Gatheral (2014) butterfly density condition g(k) >= 0 on a dense grid.

    g(k) = (1 - k w'/(2w))^2 - (w')^2/4 * (1/w + 1/4) + w''/2

    Returns (ok, min_g); ok is True when min_g >= 0 (within a small
    floating-point tolerance).
    """
    k = np.asarray(k_grid, dtype=float)
    a, b, rho, m, sigma = (params[name] for name in PARAM_NAMES)
    km = k - m
    root = np.sqrt(km * km + sigma * sigma)
    w = a + b * (rho * km + root)
    w1 = b * (rho + km / root)
    w2 = b * sigma * sigma / (root * root * root)

    g = (1.0 - k * w1 / (2.0 * w)) ** 2 - (w1 * w1) / 4.0 * (1.0 / w + 1.0 / 4.0) + w2 / 2.0
    min_g = float(np.nanmin(g))
    return bool(min_g >= -1e-12), min_g


def fit_snapshot_slices(iv_table: pd.DataFrame, n_slices: int = 3) -> list[dict]:
    """Fit SVI on the widest expiries of a cleaned ok-iv table.

    Selects the ``n_slices`` expiries with the widest k-range among those with
    >= 8 ok rows, fits w = IV^2 * T per slice, and returns a list of dicts
    with tte, n_points, k range, params, in-IV RMSE, and the butterfly check.
    """
    ok = iv_table[iv_table["iv"].notna()]
    counts = (
        ok.groupby("tte")
        .agg(n=("iv", "size"), k_min=("k", "min"), k_max=("k", "max"))
        .reset_index()
    )
    eligible = counts[counts.n >= 8].copy()
    eligible["width"] = eligible.k_max - eligible.k_min
    chosen = eligible.sort_values(["width", "n"], ascending=False).head(n_slices)

    fits = []
    for _, row in chosen.iterrows():
        slice_df = ok[ok.tte == row.tte]
        k = slice_df.k.to_numpy(float)
        T = float(row.tte)
        w = (slice_df.iv.to_numpy(float) ** 2) * T
        params = fit_svi_slice(k, w)
        model_w = svi_total_variance(params, k)
        model_iv = np.sqrt(np.maximum(model_w, 0.0) / T)
        rmse_iv = float(np.sqrt(np.mean((model_iv - slice_df.iv.to_numpy(float)) ** 2)))
        bf_ok, min_g = check_butterfly(params, np.linspace(k.min() - 0.2, k.max() + 0.2, 1001))
        fits.append(
            {
                "tte": T,
                "n_points": int(len(k)),
                "k_min": float(k.min()),
                "k_max": float(k.max()),
                "params": params,
                "rmse_in_iv": rmse_iv,
                "butterfly_ok": bf_ok,
                "min_g": min_g,
            }
        )
    return fits


def write_svi_fit_csv(fits: list[dict], out_dir: Path | str) -> Path:
    """Write one row per fitted slice: params + RMSE + butterfly result."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for f in fits:
        p = f["params"]
        rows.append(
            {
                "tte": f["tte"],
                "n_points": f["n_points"],
                "k_min": f["k_min"],
                "k_max": f["k_max"],
                "a": p["a"],
                "b": p["b"],
                "rho": p["rho"],
                "m": p["m"],
                "sigma": p["sigma"],
                "rmse_in_iv": f["rmse_in_iv"],
                "butterfly_ok": f["butterfly_ok"],
                "min_g": f["min_g"],
            }
        )
    path = out / "svi_fit.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def plot_svi_vs_interpolated(iv_table: pd.DataFrame, fits: list[dict], out_dir: Path | str) -> Path:
    """SVI fit vs the Task-09 interpolated surface cross-section per slice."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from volsurf.surface import build_surface

    ok = iv_table[iv_table["iv"].notna()]
    grid, method = build_surface(ok[["k", "tte", "iv"]])
    tri = method["interpolator"]

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    n = len(fits)
    fig, axes = plt.subplots(1, n, figsize=(6 * n, 4.5), squeeze=False)
    for ax, f in zip(axes[0], fits, strict=False):
        T = f["tte"]
        k_dense = np.linspace(f["k_min"], f["k_max"], 401)
        svi_iv = np.sqrt(np.maximum(svi_total_variance(f["params"], k_dense), 0.0) / T)
        interp_iv = tri(k_dense, np.full_like(k_dense, T))
        slice_pts = ok[ok.tte == T]
        ax.plot(k_dense, svi_iv, "-", lw=2, label="SVI fit")
        ax.plot(k_dense, interp_iv, "--", lw=1.5, label="LinearNDInterpolator")
        ax.plot(slice_pts.k, slice_pts.iv, ".", ms=3, alpha=0.5, label="cleaned ok IVs")
        ax.set_xlabel("k = log(K/S)")
        ax.set_ylabel("implied vol")
        ax.set_title(f"SVI vs interpolated, T={T:.3f}y")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)
    fig.tight_layout()
    path = out / "svi_vs_interpolated.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path
