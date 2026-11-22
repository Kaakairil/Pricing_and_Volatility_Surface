"""Reproducibility (Task 12): running the pipeline twice on the committed
snapshot produces byte-identical result CSVs.

Runs the full clean -> arbitrage -> surface -> experiments pipeline twice
into a temp directory (via the same functions ``scripts/run_pipeline.py``
uses), then compares SHA256 hashes of every output CSV against the hashes
from the first run. Seeds are fixed by construction; any nondeterminism
(unordered groupby, dict ordering, float formatting) shows up here.

Marked ``slow``: two full pipeline passes, ~2 min.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from volsurf.config_io import ROOT

SNAPSHOT = ROOT / "data" / "snapshots" / "spy_2026-11-16.csv"
CSV_NAMES = [
    "cleaned_2026-11-16.csv",
    "arbitrage_report.csv",
    "iv_table.csv",
    "iv_surface.csv",
    "surface_method.csv",
    "calendar_diagnostic.csv",
    "early_exercise_premium.csv",
    "rate_sensitivity.csv",
    "cleaning_report.csv",
]

pytestmark = pytest.mark.slow


def _hash_csv(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run_pipeline(out_dir: Path) -> dict[str, str]:
    """One full pipeline pass into out_dir; returns {csv name: sha256}."""
    import pandas as pd

    out_dir.mkdir(parents=True, exist_ok=True)

    from volsurf.arbitrage import run_checks
    from volsurf.cleaning import clean
    from volsurf.config_io import get_cleaning_rules
    from volsurf.experiments import early_exercise_premium, rate_sensitivity
    from volsurf.surface import build_surface, calendar_diagnostic, compute_iv_table

    df, meta = load_snapshot()
    meta = meta or {}
    spot, r, q = float(meta["spot"]), float(meta["rate_value"]), float(meta["dividend_yield"])
    date = str(meta["snapshot_date"])

    cleaned, removal_log = clean(
        df, spot, rules=get_cleaning_rules(ROOT / "config"), snapshot_date=date
    )
    cleaned = cleaned.dropna(subset=["mid", "tte"])
    cleaned.to_csv(out_dir / f"cleaned_{date}.csv", index=False)
    removal_log.rename(columns={"rule": "rule", "removed": "removed"}).to_csv(
        out_dir / "cleaning_report.csv", index=False
    )

    keys = ("spot", "rate_value", "dividend_yield", "snapshot_date")
    raw_report = run_checks(df, *(meta[k] for k in keys))
    cleaned_report = run_checks(cleaned, *(meta[k] for k in keys))
    pd.concat([raw_report.assign(stage="raw"), cleaned_report.assign(stage="cleaned")]).to_csv(
        out_dir / "arbitrage_report.csv", index=False, columns=["stage", *raw_report.columns]
    )

    american = compute_iv_table(cleaned, spot, r, q, style="american", steps=100)
    european = compute_iv_table(cleaned, spot, r, q, style="european")
    key = ["strike", "tte", "option"]
    iv_table = american.merge(
        european[key + ["iv"]].rename(columns={"iv": "european"}), on=key, how="left"
    ).rename(columns={"iv": "american"}).assign(iv=lambda d: d["american"])
    iv_table.to_csv(out_dir / "iv_table.csv", index=False)

    surface_in = iv_table[["k", "tte", "american"]].rename(columns={"american": "iv"})
    grid, method = build_surface(surface_in)
    grid.to_csv(out_dir / "iv_surface.csv", index=False)
    pd.DataFrame([{k: v for k, v in method.items() if k != "interpolator"}]).to_csv(
        out_dir / "surface_method.csv", index=False
    )
    calendar_diagnostic(surface_in).to_csv(out_dir / "calendar_diagnostic.csv", index=False)

    premium = early_exercise_premium(
        spot, [0.8, 0.9, 1.0, 1.1, 1.2], [1 / 52, 1 / 12, 0.25, 1.0],
        0.20, r, q, steps=1000,
    )
    premium.to_csv(out_dir / "early_exercise_premium.csv", index=False)
    rates = rate_sensitivity(
        spot, 1.0, 0.25, 0.20, [r + bp / 10_000 for bp in (-100, -50, 0, 50, 100)], q, steps=1000
    )
    rates.to_csv(out_dir / "rate_sensitivity.csv", index=False)

    return {name: _hash_csv(out_dir / name) for name in CSV_NAMES}


def load_snapshot():
    from volsurf.market_data import load_snapshot as _load

    return _load(SNAPSHOT)


def test_pipeline_twice_byte_identical(tmp_path):
    hashes1 = _run_pipeline(tmp_path / "run1")
    hashes2 = _run_pipeline(tmp_path / "run2")
    for name in CSV_NAMES:
        assert hashes1[name] == hashes2[name], (
            f"{name} differs between runs: {hashes1[name][:12]} vs {hashes2[name][:12]}"
        )


def test_committed_results_match_pipeline(tmp_path):
    """The committed results/ CSVs are the pipeline output for this snapshot."""
    committed = _run_pipeline(tmp_path / "run")
    for name in CSV_NAMES:
        committed_path = ROOT / "results" / name
        if not committed_path.exists():
            continue
        assert committed[name] == _hash_csv(committed_path), (
            f"results/{name} does not match a fresh pipeline run — "
            "re-run scripts/run_pipeline.py and commit the output"
        )
