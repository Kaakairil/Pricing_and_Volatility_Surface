"""IV table and volatility-surface interpolation (Task 09).

``compute_iv_table`` inverts each cleaned mid to American implied volatility
(binomial tree) and to a Black-Scholes (European) comparison, returning both
plus a reason code per option.  ``build_surface`` fits a C0 linear interpolant
over (log-moneyness, time-to-expiry) and evaluates it on a coarse grid;
``calendar_diagnostic`` compares total variance ``IV^2 * T`` across expiries
at fixed moneyness.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.interpolate import LinearNDInterpolator

from volsurf.implied_vol import implied_volatility

VALID_STYLES = ("american", "european")
KMIN, KMAX, TNODE = -0.5, 0.5, 0.05  # surface grid domain (log-moneyness, years)


def _validate_iv(df: pd.DataFrame, spot: float, style: str, steps: int) -> None:
    if not (isinstance(spot, (int, float)) and np.isfinite(spot) and spot > 0):
        raise ValueError(f"spot must be a finite positive number, got {spot!r}")
    if style not in VALID_STYLES:
        raise ValueError(f"style must be one of {VALID_STYLES}, got {style!r}")
    if steps < 1:
        raise ValueError(f"steps must be >= 1, got {steps}")
    missing = [c for c in ("strike", "tte", "mid", "option") if c not in df.columns]
    if missing:
        raise ValueError(f"missing required columns: {missing}")
    for c in ("strike", "tte", "mid"):
        if df[c].isna().any():
            raise ValueError(f"column {c!r} contains NaN")


def compute_iv_table(
    df: pd.DataFrame,
    spot: float,
    r: float,
    q: float,
    style: str = "american",
    steps: int = 100,
) -> pd.DataFrame:
    """Invert mid prices to implied volatility per option.

    Parameters mirror ``implied_volatility``; ``style`` defaults to American
    (SPY).  Returns one row per input option with columns ``strike, tte,
    option, mid, k, iv, reason``.  ``k = log(strike / spot)``.  Failed or
    out-of-bounds inversions yield NaN ``iv`` with a reason code (never a
    fabricated value).
    """
    _validate_iv(df, spot, style, steps)
    keep = ["strike", "tte", "option", "mid"] + (["expiry"] if "expiry" in df.columns else [])
    out = df[keep].copy()
    out["k"] = np.log(out["strike"].astype(float) / float(spot))
    ivs, reasons = [], []
    for _, row in out.iterrows():
        iv, reason = implied_volatility(
            spot, row.strike, row.tte, row.mid, r, q, row.option, style=style, steps=steps
        )
        ivs.append(iv)
        reasons.append(reason)
    out["iv"] = ivs
    out["reason"] = reasons
    return out


def build_surface(iv_table: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Interpolate scattered ``(k, tte)`` IV points over a grid.

    Returns ``(grid_df, method_info)``.  ``grid_df`` has columns ``k, tte, iv``
    over the domain ``[KMIN, KMAX] x [TNODE, ...]``.  Grid points outside the
    convex hull of the input points are NaN — never extrapolated.
    ``method_info`` records the triangulation method, input counts, NaN rows
    dropped, and the fitted k-range.
    """
    missing = [c for c in ("k", "tte", "iv") if c not in iv_table.columns]
    if missing:
        raise ValueError(f"missing required columns: {missing}")
    interior = iv_table[["k", "tte", "iv"]].dropna()
    if len(interior) < 4:
        raise ValueError(f"need at least 4 finite IV points to interpolate, got {len(interior)}")
    pts = interior[["k", "tte"]].to_numpy()
    vals = interior["iv"].to_numpy()
    tri = LinearNDInterpolator(pts, vals)
    # Coarse surface grid; TNODE floor keeps the first maturity off the hull edge.
    k_grid = np.linspace(KMIN, KMAX, 41)
    t_grid = np.linspace(TNODE, float(interior["tte"].max()), 21)
    gk, gt = np.meshgrid(k_grid, t_grid, indexing="ij")
    grid = pd.DataFrame({"k": gk.ravel(), "tte": gt.ravel()})
    grid["iv"] = tri(grid[["k", "tte"]].to_numpy())
    method = {
        "method": "LinearNDInterpolator",
        "input_rows": len(iv_table),
        "dropped_nan": int(iv_table.iv.isna().sum()),
        "n_points": len(interior),
        "col_count": len(iv_table),
        "k_min": float(interior.k.min()),
        "k_max": float(interior.k.max()),
        # Callable reproducing the input IVs exactly at their (k, tte) nodes
        # (LinearNDInterpolator interpolation property).  Not for extrapolation.
        "interpolator": tri,
    }
    return grid, method


def calendar_diagnostic(iv_table: pd.DataFrame) -> pd.DataFrame:
    """Compare total variance ``IV^2 T`` across expiries at fixed moneyness.

    Returns one row per class of comparison with columns ``k, tte_pair,
    total_var_decrease, warning``.  A drop in total variance may be a real
    calendar effect or an artifact of the C0 interpolant / model assumptions;
    ``warning`` records that the decrease is not executable-arbitrage proof.
    """
    records = []
    for k, g in iv_table.groupby("k"):
        g = g[["tte", "iv"]].dropna().sort_values("tte")
        for (t1, v1), (t2, v2) in zip(g.values[:-1], g.values[1:], strict=True):
            dec = v2**2 * t2 < v1**2 * t1
            records.append(
                {
                    "k": k,
                    "tte_pair": f"{t1:g}/{t2:g}",
                    "total_var_decrease": bool(dec),
                    "warning": bool(dec),
                }
            )
    return pd.DataFrame(records, columns=["k", "tte_pair", "total_var_decrease", "warning"])
