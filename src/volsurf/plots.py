"""Matplotlib figures for the volatility surface (Task 09).

Every function writes a PNG to ``out_dir`` and returns its path.  Plotting
is deliberately mechanical — labelled axes and honest defaults — so the
report can cite exact figures.  No interactive show; figures written only.

Not yet wired from the CLI (owned by later tasks): ``plot_error_heatmap``
(pricing verification, plan-10) and ``plot_pre_post_cleaning`` (report,
plan-12).  ponytail: add when those tasks land.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

_DAY = 365.0


def _save(fig: plt.Figure, out_dir: Path, name: str) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / name
    fig.savefig(path, dpi=144, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_smiles(iv_table: pd.DataFrame, out_dir: Path) -> list[Path]:
    """One ``smile_<expiry>.png`` per expiry: American IV vs log-moneyness.

    ``iv_table`` needs columns ``expiry, k, iv``.  Slices with fewer than two
    finite IVs still get a placeholder figure so the artifact exists.
    """
    names = []
    for expiry, g in iv_table.dropna(subset=["iv"]).groupby("expiry"):
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.scatter(g["k"], g["iv"], s=8)
        ax.set_xlabel("log-moneyness k")
        ax.set_ylabel("American IV")
        ax.set_title(f"IV smile {expiry}")
        ax.grid(alpha=0.3)
        names.append(_save(fig, out_dir, f"smile_{expiry}.png"))
    return names


def plot_term_structure(grid: pd.DataFrame, out_dir: Path) -> Path:
    """IV at fixed moneyness k = 0 (ATM) across maturity, from the grid."""
    atm = grid.dropna(subset=["iv"])
    atm = atm[np.isclose(atm["k"], 0.0, atol=1e-3)]
    fig, ax = plt.subplots(figsize=(6, 4))
    if len(atm):
        atm = atm.sort_values("tte")
        ax.plot(atm["tte"] * _DAY, atm["iv"], marker="o")
    else:
        ax.text(0.5, 0.5, "no ATM grid points", ha="center")
    ax.set_xlabel("days to expiry")
    ax.set_ylabel("IV at k = 0")
    ax.set_title("Term structure (ATM)")
    ax.grid(alpha=0.3)
    return _save(fig, out_dir, "term_structure.png")


def plot_surface_3d(grid: pd.DataFrame, out_dir: Path) -> Path:
    """3-D wire plot of the interpolated surface grid."""
    g = grid.dropna(subset=["iv"])
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection="3d")
    if len(g):
        ax.plot_trisurf(g["k"], g["tte"] * _DAY, g["iv"], cmap="viridis", linewidth=0.2)
    ax.set_xlabel("log-moneyness k")
    ax.set_ylabel("days to expiry")
    ax.set_zlabel("IV")
    ax.set_title("Volatility surface (LinearNDInterpolator)")
    return _save(fig, out_dir, "surface_3d.png")


def plot_iv_american_vs_bs(iv_table: pd.DataFrame, out_dir: Path) -> Path:
    """Scatter American IV against Black-Scholes IV with y = x reference."""
    data = iv_table.dropna(subset=["american", "european"])
    fig, ax = plt.subplots(figsize=(6, 6))
    if len(data):
        ax.scatter(data["european"], data["american"], s=6, alpha=0.5)
        hi = max(data[["american", "european"]].to_numpy().max(), 1e-9)
        ax.plot([0, hi], [0, hi], color="gray", ls="--", lw=1, label="y = x")
    else:
        ax.text(0.5, 0.5, "no finite IV pair", ha="center")
    ax.set_xlabel("Black-Scholes IV")
    ax.set_ylabel("American IV (CRR)")
    ax.set_title("American vs Black-Scholes implied vol")
    ax.grid(alpha=0.3)
    if len(data):
        ax.legend()
    return _save(fig, out_dir, "iv_american_vs_bs.png")
