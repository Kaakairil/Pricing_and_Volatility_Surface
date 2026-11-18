"""Local no-arbitrage screens for American option quotes."""

from datetime import date
from math import exp, isfinite

import numpy as np
import pandas as pd

from volsurf.cleaning import compute_tte

_COLUMNS = [
    "expiry",
    "check",
    "input_quotes",
    "eligible_quotes",
    "tested",
    "midpoint_flags",
    "spread_robust_flags",
    "sample_strikes",
]


def run_checks(
    df: pd.DataFrame, spot: float, r: float, q: float, snapshot_date: str, tol: float = 1e-8
) -> pd.DataFrame:
    """Summarize local quote comparisons per expiry under nonnegative carry.

    Exclude invalid quotes and ambiguous duplicate keys. Distances and tolerance
    are in option price units; zero tested comparisons do not imply a pass.
    """
    for name, value in (("spot", spot), ("r", r), ("q", q), ("tol", tol)):
        if not isinstance(value, (int, float)) or not isfinite(value) or value < 0:
            raise ValueError(f"{name} must be finite and nonnegative")
    if spot == 0:
        raise ValueError("spot must be positive")
    try:
        snapshot_date = date.fromisoformat(snapshot_date).isoformat()
    except (TypeError, ValueError) as exc:
        raise ValueError("snapshot_date must be an ISO date") from exc

    keys = ["expiry", "strike", "option"]
    required = keys + ["bid", "ask"]
    if missing := set(required).difference(df.columns):
        raise ValueError(f"Missing quote columns: {', '.join(sorted(missing))}")
    quotes = df[required].copy()
    quotes["expiry"] = (
        pd.to_datetime(quotes["expiry"], errors="coerce", utc=True)
        .dt.tz_localize(None)
        .dt.normalize()
    )
    quotes["tte"] = compute_tte(quotes, snapshot_date)
    numeric = ["strike", "bid", "ask"]
    quotes[numeric] = quotes[numeric].apply(pd.to_numeric, errors="coerce").astype(float)
    eligible = (
        np.isfinite(quotes[numeric]).all(axis=1)
        & (quotes.strike > 0)
        & (quotes.bid > 0)
        & (quotes.ask >= quotes.bid)
        & (quotes.tte > 0)
        & quotes.option.isin(["call", "put"])
        & ~quotes.duplicated(keys, keep=False)
    )
    quotes["mid"] = quotes.bid / 2 + quotes.ask / 2
    quotes["eligible"] = eligible

    rows = []
    for expiry, group in quotes.groupby("expiry", dropna=False):
        valid = group[group.eligible].sort_values("strike")
        call = valid[valid.option == "call"].set_index("strike")
        put = valid[valid.option == "put"].set_index("strike")
        date_label = "invalid" if pd.isna(expiry) else expiry.date().isoformat()

        def record(name, strikes, midpoint, robust, _group=group, _valid=valid, _label=date_label):
            # ponytail: first three midpoint flags; add a detail table if reviewers need every leg.
            sample = ";".join(strikes[i] for i in np.flatnonzero(midpoint)[:3])
            rows.append(
                (
                    _label,
                    name,
                    len(_group),
                    len(_valid),
                    len(strikes),
                    int(midpoint.sum()),
                    int(robust.sum()),
                    sample,
                )
            )

        pairs = call.join(put, how="inner", lsuffix="_call", rsuffix="_put")
        K = pairs.index.to_numpy()
        T = group.tte.iloc[0] if len(pairs) else 0.0
        lower = spot * exp(-q * T) - K
        upper = spot - K * exp(-r * T)
        mid = pairs.mid_call - pairs.mid_put
        record(
            "american_parity",
            [f"{k:g}" for k in K],
            (mid < lower - tol) | (mid > upper + tol),
            (pairs.ask_call - pairs.bid_put < lower - tol)
            | (pairs.bid_call - pairs.ask_put > upper + tol),
        )

        # In each vertical, the first leg should be worth at least the second.
        for side, chain in (("call", call), ("put", put.iloc[::-1])):
            k = chain.index.to_numpy()
            bid, ask, mid = chain[["bid", "ask", "mid"]].to_numpy().T
            record(
                f"{side}_monotonicity",
                [f"{min(a, b):g}/{max(a, b):g}" for a, b in zip(k[:-1], k[1:], strict=True)],
                mid[1:] - mid[:-1] > tol,
                bid[1:] - ask[:-1] > tol,
            )

        k = call.index.to_numpy()
        bid, ask, mid = call[["bid", "ask", "mid"]].to_numpy().T
        weight = (k[2:] - k[1:-1]) / (k[2:] - k[:-2])
        record(
            "call_convexity",
            [f"{a:g}/{b:g}/{c:g}" for a, b, c in zip(k[:-2], k[1:-1], k[2:], strict=True)],
            mid[1:-1] - (weight * mid[:-2] + (1 - weight) * mid[2:]) > tol,
            bid[1:-1] - (weight * ask[:-2] + (1 - weight) * ask[2:]) > tol,
        )

    return pd.DataFrame(rows, columns=_COLUMNS)
