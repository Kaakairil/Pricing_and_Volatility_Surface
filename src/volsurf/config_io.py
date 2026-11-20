"""Load runtime thresholds from the committed YAML config files.

Keeps pipeline thresholds in ``config/*.yaml`` (the single source of truth)
instead of hardcoded in source.  Nothing here touches the network.
"""

from __future__ import annotations

from pathlib import Path

import yaml

# Repo root = two levels up from this file (src/volsurf/config_io.py).
ROOT = Path(__file__).resolve().parents[2]

# Rule keys the cleaning pipeline consumes, in the order STEPS in cleaning.py.
CLEANING_KEYS = (
    "max_spread_pct_of_mid",
    "min_open_interest",
    "min_volume",
    "min_t_days",
    "moneyness_min",
    "moneyness_max",
)

DEFAULT_CLEANING_RULES = {
    "max_spread_pct_of_mid": 0.50,
    "min_open_interest": 100,
    "min_volume": 1,
    "min_t_days": 7,
    "moneyness_min": 0.7,
    "moneyness_max": 1.3,
}


def get_cleaning_rules(config_dir: str | Path | None = None) -> dict:
    """Load the six cleaning thresholds from ``config/cleaning.yaml``.

    With no argument the committed ``ROOT / "config"`` directory is used.
    Returns a dict with exactly the ``CLEANING_KEYS``.  A missing key or a
    non-numeric value falls back to the default for that key, so a partial or
    hand-edited config never crashes the pipeline.
    """
    path = Path(config_dir or ROOT / "config") / "cleaning.yaml"
    rules = dict(DEFAULT_CLEANING_RULES)
    if path.exists():
        loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for key in CLEANING_KEYS:
            if isinstance(loaded.get(key), (int, float)):
                rules[key] = float(loaded[key])
    return rules
