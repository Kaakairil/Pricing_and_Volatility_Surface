"""Market/config files load with numeric values for downstream calculations."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_pricing_grid_maturities_are_numeric_year_fractions():
    grid = yaml.safe_load((ROOT / "config/pricing_grid.yaml").read_text(encoding="utf-8"))
    maturities = grid["maturity_years"]
    assert all(isinstance(t, float) for t in maturities)
    assert maturities == [1 / 52, 1 / 12, 0.25, 1.0]
