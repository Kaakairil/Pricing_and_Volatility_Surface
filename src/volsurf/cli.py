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

Later commands (arbitrage, surface, report) attach here as their modules
land in Tasks 08-12.
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


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m volsurf.cli", description=__doc__)
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    c = sub.add_parser("clean", help="clean a snapshot via config/cleaning.yaml")
    c.add_argument("input", help="snapshot CSV (data/snapshots/spy_<date>.csv)")
    c.add_argument("-o", "--output", default="results", help="output dir (default results/)")
    c.set_defaults(handler=cmd_clean)

    f = sub.add_parser("fetch", help="manual live snapshot fetch (network)")
    f.set_defaults(handler=cmd_fetch)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.handler(args)  # dispatcher dict: subparser -> handler


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
