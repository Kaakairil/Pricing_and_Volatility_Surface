"""SNP 500 ETF (SPY) options and rate data.

These functions touch the network (yfinance / FRED) and are used for the
manual ``make fetch`` step only.  Unit tests must not call them; the
``network`` pytest marker guards that.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path

import pandas as pd
import yfinance as yf
from pandas import DataFrame


def fetch_chain(ticker: str) -> tuple[DataFrame, float, str]:
    """Fetch ``ticker`` options chain from Yahoo Finance.

    Returns
    -------
    (options_df, spot, fetch_time_utc) : tuple[DataFrame, float, str]
        ``options_df`` contains all expiries, calls and puts concatenated with
        columns ``strike, lastPrice, bid, ask, volume, openInterest,
        impliedVolatility, option, expiry``.  ``spot`` is the current Yahoo
        quote; ``fetch_time_utc`` is an ISO-8601 UTC timestamp of the fetch.

    Notes
    -----
    Record the exact fetch time and the spot quote at that moment; the
    snapshot date is derived from the record, not passed in.
    """
    t = yf.Ticker(ticker)
    spot = float(t.info["regularMarketPrice"])
    pages = []
    for expiry in t.options:
        chain = t.option_chain(expiry)
        for opt in ("calls", "puts"):
            df = getattr(chain, opt).copy()
            df["option"] = opt[:-1]  # "call" / "put"
            df["expiry"] = expiry
            pages.append(df)
    df = pd.concat(pages, ignore_index=True)
    fetch_time_utc = str(_dt.datetime.now(_dt.UTC).isoformat())
    return df, spot, fetch_time_utc


def save_snapshot(options_df: DataFrame, meta: dict, out_dir) -> Path:
    """Write the chain + metadata + SHA256 checksum sidecar.

    Parameters
    ----------
    options_df : DataFrame
        Chain as produced by ``fetch_chain`` (or a synthetic stand-in in tests).
    meta : dict
        Provenance metadata (ticker, snapshot_date, fetch_time_utc, spot,
        rate_value, rate_source, dividend_yield, dividend_method, row_counts…).
    out_dir : path-like
        Directory to write into (created if missing).

    Returns
    -------
    Path
        The CSV path.  An adjacent ``<name>.metadata.json`` and
        ``<name>.sha256`` sidecar are also written.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    date = meta.get("snapshot_date", "none")
    name = f"spy_{date}"
    csv_path = out_dir / f"{name}.csv"
    options_df.to_csv(csv_path, index=False)

    meta_path = csv_path.with_suffix(".metadata.json")
    meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True), encoding="utf-8")

    digest = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    csv_path.with_suffix(".sha256").write_text(f"{digest}\n", encoding="utf-8")
    return csv_path


def load_snapshot(path) -> tuple[DataFrame, dict]:
    """Load a snapshot written by ``save_snapshot``, verifying the SHA256.

    Parameters
    ----------
    path : path-like
        The snapshot CSV (or a ``.metadata.json`` / ``.sha256`` sibling).

    Returns
    -------
    (options_df, meta) : tuple[DataFrame, dict]

    Raises
    ------
    ValueError
        If the CSV bytes do not match the recorded SHA256 (tampered or
        truncated snapshot).
    """
    path = Path(path)
    if path.suffix == ".json" or path.suffix == ".sha256":
        path = path.with_suffix(".csv")
    digest_file = path.with_suffix(".sha256")
    if not digest_file.exists():
        raise ValueError(f"missing checksum sidecar for {path!s}")
    recorded = digest_file.read_text(encoding="utf-8").strip()
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if recorded != actual:
        raise ValueError(
            f"checksum mismatch for {path!s}: recorded {recorded[:16]}…, "
            f"actual {actual[:16]}… (snapshot tampered or truncated)"
        )
    df = pd.read_csv(path)
    meta_path = path.with_suffix(".metadata.json")
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    return df, meta
