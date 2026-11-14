---
description: Task 6 — market data fetch, snapshot, checksum
---

# Task 6: Market Data (FR-6)

## Files
- `src/volsurf/market_data.py`, `tests/test_market_data.py`

## Interfaces
- `fetch_chain(ticker, date) -> DataFrame` — raw option chain via yfinance, all expirations, calls+puts; spot, dividend yield, r recorded alongside.
- `save_snapshot(df, meta) -> path` — write to `data/raw/`, timestamp + SHA256 checksum + provenance (ticker, date, fetched-at, package versions).
- `load_snapshot(path) -> (df, meta)` — verifies checksum on reload; raises on mismatch.

## Steps
- [ ] Tests: snapshot checksum round-trip passes; tampered file fails load; provenance fields present.
- [ ] Implement fetch: yfinance `Ticker(ticker).options`, per-expiry chain, concat. Record spot (`history` last close), dividend yield (annual div / spot, documented), rate from `config/market.yaml` (record source/date).
- [ ] Implement save/load with `hashlib.sha256` over file bytes + `json` meta sidecar.
- [ ] Fetch one real SPY snapshot, save it, verify reload. Commit.
