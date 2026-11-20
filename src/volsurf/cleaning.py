"""Option-chain cleaning (PRD §6.5): threshold filters + mid transformation.

Pipeline order (each step logs how many rows it removed):
  1. invalid quotes: bid or ask <= 0, crossed (bid > ask), or NaN
  2. relative bid/ask spread > ``max_spread_pct_of_mid``
  3. mid = (bid + ask) / 2  (transform, removes nothing)
  4. liquidity: openInterest >= ``min_open_interest`` and volume >= ``min_volume``
  5. minimum time to expiry >= ``min_t_days``
  6. moneyness band: ``moneyness_min`` <= K / S <= ``moneyness_max``

When ``clean`` is called with ``rules=None`` it loads the thresholds from
``config/cleaning.yaml`` via :func:`volsurf.config_io.get_cleaning_rules`;
tests inject a ``rules`` dict directly to prove thresholds are not hardcoded.
"""

from __future__ import annotations

import math

import pandas as pd

from volsurf.config_io import get_cleaning_rules

REQUIRED_COLUMNS = ["strike", "expiry", "bid", "ask", "openInterest", "volume"]

# step name -> rule keys it consumes ("" for the purely additive mid step)
STEPS = [
    ("zero_quotes", ""),
    ("max_spread_pct_of_mid", "max_spread_pct_of_mid"),
    ("mid", ""),
    ("liquidity", "min_open_interest,min_volume"),
    ("min_t_days", "min_t_days"),
    ("moneyness", "moneyness_min,moneyness_max"),
]


def compute_moneyness(df: pd.DataFrame, spot: float) -> pd.Series:
    """Moneyness K / S for each row. Requires ``strike`` column."""
    return df["strike"].astype(float) / float(spot)


def compute_tte(df: pd.DataFrame, snapshot_date: str | pd.Timestamp) -> pd.Series:
    """Years to expiry on a 365-day basis (PRD §6.4.1: calendar days)."""
    expiry = pd.to_datetime(df["expiry"])
    snap = pd.to_datetime(snapshot_date)
    return (expiry - snap).dt.days / 365.0


def _validate_input(df: pd.DataFrame) -> pd.DataFrame:
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Input missing required columns: {missing}")
    try:
        df["strike"] = df["strike"].astype(float)
    except (TypeError, ValueError) as exc:
        raise ValueError("Column 'strike' must be numeric") from exc
    return df


def clean(
    df: pd.DataFrame,
    spot: float,
    rules: dict | None = None,
    snapshot_date: str | pd.Timestamp = None,
    log_path: str | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Apply the PRD §6.5 cleaning pipeline.

    Returns ``(cleaned, log)`` where ``log`` has one row per pipeline step with
    ``rule`` (step name) and ``removed`` (row count). Never mutates ``df``.
    If ``snapshot_date`` is None, moneyness is still computed (no tte filter
    applies); callers should always pass it for real snapshots.
    """
    if rules is None:
        rules = get_cleaning_rules()  # production: config/cleaning.yaml
    merged = {**get_cleaning_rules(), **rules}

    if not (isinstance(spot, (int, float)) and math.isfinite(spot) and spot > 0):
        raise ValueError(f"spot must be a finite positive number, got {spot!r}")

    df = _validate_input(df.copy(deep=True))

    log = pd.DataFrame({"rule": [s for s, _ in STEPS], "removed": [0] * len(STEPS)})

    def _drop(mask: pd.Series, idx: int) -> pd.DataFrame:
        nonlocal df
        removed = int((~mask).sum())
        log.loc[idx, "removed"] = removed
        return df.loc[mask]

    # 1. non-positive quotes (zero bid OR zero ask are both untradeable);
    #    crossed quotes (bid > ask) are invalid two-sided quotes too — the
    #    arbitrage module treats them as ineligible, and their mid is not a
    #    meaningful price. A locked market (bid == ask) is kept.
    q = (df["bid"] > 0) & (df["ask"] >= df["bid"])
    # NaN in quote columns means no quote -> remove
    q = q & df["bid"].notna() & df["ask"].notna()
    df = _drop(q, 0)

    # 2. relative spread vs mid (only for rows that still have quotes)
    mid = 0.5 * (df["bid"] + df["ask"]).astype(float)
    spread_pct = (df["ask"].astype(float) - df["bid"].astype(float)) / mid
    df = _drop(spread_pct <= merged["max_spread_pct_of_mid"], 1)

    # 3. mid transformation (additive, nothing removed)
    df["mid"] = 0.5 * (df["bid"] + df["ask"]).astype(float)
    log.loc[2, "removed"] = 0

    # 4. liquidity: OI and volume floors applied together
    oi = (df["openInterest"] >= merged["min_open_interest"]) & df["openInterest"].notna()
    vol = (df["volume"] >= merged["min_volume"]) & df["volume"].notna()
    df = _drop(oi & vol, 3)

    # 5. minimum days to expiry
    if snapshot_date is not None:
        tte_days = (pd.to_datetime(df["expiry"]) - pd.to_datetime(snapshot_date)).dt.days
        df = _drop(tte_days >= merged["min_t_days"], 4)
        df["tte"] = tte_days.loc[df.index] / 365.0
    else:
        log.loc[4, "removed"] = 0

    # 6. moneyness band (inclusive edges)
    moneyness = compute_moneyness(df, spot)
    df["moneyness"] = moneyness
    in_band = (moneyness >= merged["moneyness_min"]) & (moneyness <= merged["moneyness_max"])
    df = _drop(in_band, 5)

    if log_path is not None:
        log.to_csv(log_path, index=False)

    return df, log
