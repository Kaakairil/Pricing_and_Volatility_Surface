"""Full offline pipeline from the committed snapshot (``make all``).

clean -> arbitrage -> surface -> experiments -> figures. Network is never
touched: input is the committed snapshot in ``data/snapshots/``.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from volsurf.arbitrage import run_checks
from volsurf.cleaning import clean
from volsurf.config_io import ROOT, get_cleaning_rules
from volsurf.experiments import early_exercise_premium, rate_sensitivity
from volsurf.market_data import load_snapshot
from volsurf.plots import (
    plot_iv_american_vs_bs,
    plot_smiles,
    plot_surface_3d,
    plot_term_structure,
)
from volsurf.surface import build_surface, calendar_diagnostic, compute_iv_table

RESULTS = ROOT / "results"
FIG_DIR = RESULTS / "surface"

SNAPSHOT = ROOT / "data" / "snapshots" / "spy_2026-11-16.csv"

# PRD §9.2 experiment grid (RQ2), documented fallback ATM sigma
S = 754.37
MONEYNESS = [0.8, 0.9, 1.0, 1.1, 1.2]
T_GRID = [1 / 52, 1 / 12, 0.25, 1.0]
SIGMA = 0.20
R = 0.04219617863034214
Q = 0.007477573830616421
R_GRID = [0.04219617863034214 + bp / 10_000 for bp in (-100, -50, 0, 50, 100)]


def main() -> None:
    df, meta = load_snapshot(SNAPSHOT)
    meta = meta or {}
    spot = float(meta["spot"])
    r = float(meta["rate_value"])
    q = float(meta["dividend_yield"])
    date = str(meta["snapshot_date"])

    # 1. clean
    cleaned, _ = clean(df, spot, rules=get_cleaning_rules(ROOT / "config"), snapshot_date=date)
    cleaned = cleaned.dropna(subset=["mid", "tte"])
    cleaned.to_csv(RESULTS / f"cleaned_{date}.csv", index=False)

    # 2. arbitrage raw vs cleaned
    keys = ("spot", "rate_value", "dividend_yield", "snapshot_date")
    raw_report = run_checks(df, *(meta[k] for k in keys))
    cleaned_report = run_checks(cleaned, *(meta[k] for k in keys))
    pd.concat([raw_report.assign(stage="raw"), cleaned_report.assign(stage="cleaned")]).to_csv(
        RESULTS / "arbitrage_report.csv", index=False, columns=["stage", *raw_report.columns]
    )

    # 3. IV table + surface
    american = compute_iv_table(cleaned, spot, r, q, style="american", steps=100)
    european = compute_iv_table(cleaned, spot, r, q, style="european")
    key = ["strike", "tte", "option"]
    iv_table = american.merge(
        european[key + ["iv"]].rename(columns={"iv": "european"}), on=key, how="left"
    ).rename(columns={"iv": "american"})
    iv_table = iv_table.assign(iv=iv_table["american"])
    iv_table.to_csv(RESULTS / "iv_table.csv", index=False)

    surface_in = iv_table[["k", "tte", "american"]].rename(columns={"american": "iv"})
    grid, method = build_surface(surface_in)
    grid.to_csv(RESULTS / "iv_surface.csv", index=False)
    pd.DataFrame([{k: v for k, v in method.items() if k != "interpolator"}]).to_csv(
        RESULTS / "surface_method.csv", index=False
    )
    calendar_diagnostic(surface_in).to_csv(RESULTS / "calendar_diagnostic.csv", index=False)

    # 4. experiments (RQ2): early-exercise premium + rate sensitivity
    premium = early_exercise_premium(spot, MONEYNESS, T_GRID, SIGMA, R, Q, steps=1000)
    premium.to_csv(RESULTS / "early_exercise_premium.csv", index=False)
    rates = rate_sensitivity(spot, 1.0, 0.25, SIGMA, R_GRID, Q, steps=1000)
    rates.to_csv(RESULTS / "rate_sensitivity.csv", index=False)

    # 5. figures
    plot_smiles(iv_table, FIG_DIR)
    plot_term_structure(grid, FIG_DIR)
    plot_surface_3d(grid, FIG_DIR)
    plot_iv_american_vs_bs(iv_table, FIG_DIR)

    print(f"pipeline complete -> {RESULTS}")


if __name__ == "__main__":
    main()
