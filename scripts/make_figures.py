"""Regenerate all figures from committed result CSVs (``make figures``).

Reads results/iv_table.csv and results/iv_surface.csv — no snapshot needed.
"""

from __future__ import annotations

import pandas as pd

from volsurf.config_io import ROOT
from volsurf.plots import (
    plot_iv_american_vs_bs,
    plot_smiles,
    plot_surface_3d,
    plot_term_structure,
)

RESULTS = ROOT / "results"
FIG_DIR = RESULTS / "surface"


def main() -> None:
    iv_table = pd.read_csv(RESULTS / "iv_table.csv")
    grid = pd.read_csv(RESULTS / "iv_surface.csv")
    plot_smiles(iv_table, FIG_DIR)
    plot_term_structure(grid, FIG_DIR)
    plot_surface_3d(grid, FIG_DIR)
    plot_iv_american_vs_bs(iv_table, FIG_DIR)
    print(f"figures -> {FIG_DIR}")


if __name__ == "__main__":
    main()
