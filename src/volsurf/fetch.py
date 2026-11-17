"""Manual live snapshot fetch (``make fetch``).

Fetches the SPY options chain from Yahoo Finance, the 3-month T-bill
discount rate (DTB3) from FRED, and the trailing dividend yield, then
writes a committed snapshot to ``data/snapshots/`` and fills
``config/market.yaml``.

Run only at/after market hours (quotes are unreliable off-hours).  This
is a network step — it is *not* part of ``make all``.
"""

from __future__ import annotations

from pathlib import Path as _Path

import requests
import yaml
import yfinance as yf

from volsurf import __version__
from volsurf.market_data import fetch_chain, save_snapshot
from volsurf.rates import dividend_yield_continuous, risk_free_from_dtb3

ROOT = _Path(__file__).resolve().parents[2]  # repo root
CONFIG = ROOT / "config" / "market.yaml"
SNAPSHOT_DIR = ROOT / "data" / "snapshots"

FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DTB3"


def _latest_dtb3() -> tuple[float, str]:
    """Latest non-empty DTB3 discount rate (decimal) and its observation date."""
    resp = requests.get(FRED_CSV, timeout=20)
    resp.raise_for_status()
    lines = resp.text.strip().splitlines()
    for line in reversed(lines[1:]):
        date, _, value = line.partition(",")
        if value.strip():
            return float(value), date
    raise RuntimeError("no DTB3 observation found in FRED response")


def _trailing_dividend(ticker: str) -> float:
    """Trailing 12-month dividend per share from Yahoo info."""
    info = yf.Ticker(ticker).info
    value = info.get("trailingAnnualDividendRate")
    if value is None:
        raise RuntimeError(f"no trailingAnnualDividendRate for {ticker}")
    return float(value)


def main() -> None:
    ticker = "SPY"
    dtb3, dtb3_date = _latest_dtb3()
    rate = risk_free_from_dtb3(dtb3 / 100.0, tenor_days=91)  # FRED quotes in percent

    options_df, spot, fetch_time_utc = fetch_chain(ticker)
    trailing = _trailing_dividend(ticker)
    dividend = dividend_yield_continuous(trailing, spot)

    snapshot_date = fetch_time_utc[:10]  # YYYY-MM-DD of the fetch
    meta = {
        "ticker": ticker,
        "snapshot_date": snapshot_date,
        "fetch_time_utc": fetch_time_utc,
        "spot": float(spot),
        "spot_source": "yfinance regularMarketPrice at fetch_time_utc (no quote timestamp exposed)",
        "rate_value": float(rate),
        "rate_source": f"FRED DTB3 {dtb3_date}",
        "rate_tenor_days": 91,
        "dividend_yield": float(dividend),
        "dividend_method": "trailing_12m",
        "trailing_12m_dividends": trailing,
        "package_versions": {
            "volsurf": __version__,
            "yfinance": yf.__version__,
        },
        "row_counts": {
            "total": int(len(options_df)),
            "calls": int((options_df["option"] == "call").sum()),
            "puts": int((options_df["option"] == "put").sum()),
            "expiries": int(options_df["expiry"].nunique()),
        },
    }

    path = save_snapshot(options_df, meta, SNAPSHOT_DIR)
    print(f"snapshot written: {path}")
    print(f"rows: {meta['row_counts']}")

    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8")) or {}
    config["ticker"] = ticker
    config["snapshot_date"] = snapshot_date
    config["fetch_time_utc"] = fetch_time_utc
    config["rate_value"] = float(rate)
    config["rate_source"] = meta["rate_source"]
    config["dividend_yield"] = float(dividend)
    with open(CONFIG, "w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, sort_keys=False)
    print(f"config updated: {CONFIG}")


if __name__ == "__main__":
    main()
