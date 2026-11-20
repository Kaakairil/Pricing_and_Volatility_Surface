"""Config IO (Task 07 Option A): thresholds load from config/cleaning.yaml.

Guards against the previous gap where ``config/cleaning.yaml`` existed but was
never actually read — cleaning relied on a hardcoded mirror. These tests
prove production defaults come from the YAML file on disk.
"""

from pathlib import Path

from volsurf.config_io import (
    CLEANING_KEYS,
    DEFAULT_CLEANING_RULES,
    get_cleaning_rules,
)

ROOT = Path(__file__).resolve().parents[1]


def test_yaml_thresholds_match_default_keys():
    rules = get_cleaning_rules(ROOT / "config")
    assert set(rules) == set(CLEANING_KEYS)


def test_yaml_values_are_the_committed_thresholds():
    rules = get_cleaning_rules(ROOT / "config")
    assert rules["max_spread_pct_of_mid"] == 0.50
    assert rules["min_open_interest"] == 100
    assert rules["min_volume"] == 1
    assert rules["min_t_days"] == 7
    assert rules["moneyness_min"] == 0.7
    assert rules["moneyness_max"] == 1.3


def test_missing_config_file_falls_back_to_defaults(tmp_path):
    # Directory with no cleaning.yaml -> defaults, no crash.
    rules = get_cleaning_rules(tmp_path)
    assert rules == DEFAULT_CLEANING_RULES


def test_partial_config_keeps_unset_defaults(tmp_path):
    (tmp_path / "cleaning.yaml").write_text("min_open_interest: 500\n", encoding="utf-8")
    rules = get_cleaning_rules(tmp_path)
    assert rules["min_open_interest"] == 500.0
    assert rules["min_t_days"] == 7.0  # untouched -> default


def test_bare_call_reads_the_real_yaml_not_defaults():
    # config_io.get_cleaning_rules() with no argument resolved ROOT (repo
    # root) instead of ROOT/config — the YAML was never read and callers got
    # the fallback defaults. YAML values pass through float(), so the loaded
    # dict has float min_open_interest; the int-typed default would betray
    # a fallback.
    rules = get_cleaning_rules()
    assert isinstance(rules["min_open_interest"], float)
    assert rules == get_cleaning_rules(ROOT / "config")
