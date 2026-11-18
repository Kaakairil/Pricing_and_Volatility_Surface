"""VolSurf CLI: pipeline steps reachable from the committed repository.

Commands implemented so far (matching the Makefile targets that exist today):

    python -m volsurf.cli clean <snapshot.csv> [-o results/]
        Apply PRD §6.5 cleaning to a persisted snapshot. Reads spot and
        snapshot date from the snapshot metadata, thresholds from
        ``config/cleaning.yaml``. Writes ``results/cleaning_report.csv`` and
        ``results/cleaned_<date>.csv``.

    python -m volsurf.cli fetch
        Manual live snapshot fetch (network, market hours). Equivalent to
        ``python -m volsurf.fetch``.

    python -m volsurf.cli arbitrage <snapshot.csv> [-o results/]
        Compare raw and cleaned American option quotes offline.

    python -m volsurf.cli surface <snapshot.csv> [-o results/]
        Build the implied-volatility surface offline. Cleans the snapshot,
        inverts mids to American + Black-Scholes IV, interpolates over
        (log-moneyness, time-to-expiry), and writes iv_table.csv, the
        calendar diagnostic, and the surface figures. Missing rate/dividend
        metadata falls back to zero (documented in the write-up).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from volsurf import __version__


def _fail(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(2)


def cmd_fetch(args: argparse.Namespace) -> int:
    """Manual live snapshot fetch (network step, market hours)."""
    from volsurf.fetch import main as fetch_main

    fetch_main()
    return 0


def cmd_clean(args: argparse.Namespace) -> int:
    """Clean a persisted snapshot per PRD §6.5, thresholds from config."""
    from volsurf.cleaning import clean
    from volsurf.config_io import get_cleaning_rules
    from volsurf.market_data import load_snapshot

    snapshot = Path(args.input)
    if not snapshot.exists():
        _fail(f"snapshot not found: {snapshot}")

    df, meta = load_snapshot(snapshot)  # verifies the SHA256 checksum
    spot = meta["spot"]
    date = meta["snapshot_date"]
    rules = get_cleaning_rules()
    Path(args.output).mkdir(parents=True, exist_ok=True)

    cleaned, log = clean(
        df,
        spot=spot,
        rules=rules,
        snapshot_date=date,
        log_path=str(Path(args.output) / "cleaning_report.csv"),
    )
    out_csv = Path(args.output) / f"cleaned_{date}.csv"
    cleaned.to_csv(out_csv, index=False)

    print(f"cleaned {len(df)} -> {len(cleaned)} rows (spot {spot}, date {date}): {out_csv}")
    print(f"removal log -> {Path(args.output) / 'cleaning_report.csv'}")
    for _, row in log.iterrows():
        print(f"  {row.rule}: removed {row.removed}")
    return 0


def cmd_surface(args: argparse.Namespace) -> int:
    """Clean snapshot, invert IV (American + BS), build surface + figures."""
    import pandas as pd

    from volsurf.cleaning import clean
    from volsurf.config_io import ROOT, get_cleaning_rules
    from volsurf.market_data import load_snapshot
    from volsurf.plots import (
        plot_iv_american_vs_bs,
        plot_smiles,
        plot_surface_3d,
        plot_term_structure,
    )
    from volsurf.surface import (
        build_surface,
        calendar_diagnostic,
        compute_iv_table,
    )

    try:
        df, meta = load_snapshot(args.input)
        meta = meta or {}
        spot = float(meta.get("spot", 0.0))
        r = float(meta.get("rate_value", 0.0))
        q = float(meta.get("dividend_yield", 0.0))
        date = str(meta.get("snapshot_date", ""))
        cleaned, _ = clean(
            df,
            spot,
            rules=get_cleaning_rules(ROOT / "config"),
            snapshot_date=date or None,
        )
        cleaned = cleaned.dropna(subset=["mid", "tte"])
        american = compute_iv_table(cleaned, spot, r, q, style="american", steps=100)
        european = compute_iv_table(cleaned, spot, r, q, style="european")
        key = ["strike", "tte", "option"]
        iv_table = american.merge(
            european[key + ["iv"]].rename(columns={"iv": "european"}),
            on=key,
            how="left",
        ).rename(columns={"iv": "american"})

        out = Path(args.output)
        out.mkdir(parents=True, exist_ok=True)
        iv_table = iv_table.assign(iv=iv_table["american"])
        iv_table.to_csv(out / "iv_table.csv", index=False)

        surface_in = iv_table[["k", "tte", "american"]].rename(columns={"american": "iv"})
        grid, method = build_surface(surface_in)
        grid.to_csv(out / "iv_surface.csv", index=False)
        method_csv = {
            k: v for k, v in method.items() if k != "interpolator"
        }  # not JSON-serializable
        pd.DataFrame([method_csv]).to_csv(out / "surface_method.csv", index=False)
        calendar_diagnostic(surface_in).to_csv(out / "calendar_diagnostic.csv", index=False)

        fig_dir = out / "surface"
        plot_smiles(iv_table, fig_dir)
        plot_term_structure(grid, fig_dir)
        plot_surface_3d(grid, fig_dir)
        plot_iv_american_vs_bs(iv_table, fig_dir)
    except (OSError, ValueError, TypeError) as exc:
        _fail(str(exc))
    print(f"surface -> {out / 'iv_table.csv'}, figures -> {fig_dir}")
    return 0


def cmd_arbitrage(args: argparse.Namespace) -> int:
    """Write raw and cleaned quote diagnostics for one local snapshot."""
    import pandas as pd

    from volsurf.arbitrage import run_checks
    from volsurf.cleaning import clean
    from volsurf.config_io import ROOT, get_cleaning_rules
    from volsurf.market_data import load_snapshot

    keys = ("spot", "rate_value", "dividend_yield", "snapshot_date")
    try:
        df, meta = load_snapshot(args.input)
        if missing := [key for key in keys if key not in meta]:
            raise ValueError(f"Missing snapshot metadata: {', '.join(missing)}")
        raw = run_checks(df, *(meta[key] for key in keys))
        cleaned, _ = clean(
            df,
            meta["spot"],
            rules=get_cleaning_rules(ROOT / "config"),
            snapshot_date=meta["snapshot_date"],
        )
        filtered = run_checks(cleaned, *(meta[key] for key in keys))
        report = pd.concat([raw.assign(stage="raw"), filtered.assign(stage="cleaned")])
        output = Path(args.output) / "arbitrage_report.csv"
        output.parent.mkdir(parents=True, exist_ok=True)
        report.to_csv(output, index=False, columns=["stage", *raw.columns])
    except (OSError, ValueError, TypeError) as exc:
        _fail(str(exc))
    print(f"quote diagnostics -> {output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m volsurf.cli", description=__doc__)
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    c = sub.add_parser("clean", help="clean a snapshot via config/cleaning.yaml")
    c.add_argument("input", help="snapshot CSV (data/snapshots/spy_<date>.csv)")
    c.add_argument("-o", "--output", default="results", help="output dir (default results/)")
    c.set_defaults(handler=cmd_clean)

    a = sub.add_parser("arbitrage", help="screen raw and cleaned American option quotes")
    a.add_argument("input", help="snapshot CSV (data/snapshots/spy_<date>.csv)")
    a.add_argument("-o", "--output", default="results", help="output dir (default results/)")
    a.set_defaults(handler=cmd_arbitrage)

    s = sub.add_parser("surface", help="build the implied-volatility surface offline")
    s.add_argument("input", help="snapshot CSV (data/snapshots/spy_<date>.csv)")
    s.add_argument("-o", "--output", default="results", help="output dir (default results/)")
    s.set_defaults(handler=cmd_surface)

    f = sub.add_parser("fetch", help="manual live snapshot fetch (network)")
    f.set_defaults(handler=cmd_fetch)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.handler(args)  # dispatcher dict: subparser -> handler


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
