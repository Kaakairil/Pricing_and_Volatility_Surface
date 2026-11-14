# Task 06: Market Data, Rates, Snapshot

**Source:** Master Plan Part E Task 06 (Review B.2, B.3, B.5) | Implements: FR-6

## Key corrections
- **B.2:** `fetch_chain(ticker)` takes NO date — yfinance returns only current chain. Snapshot date = fetch date; record exact fetch time (UTC) + spot timestamp. Refuse to write snapshot whose recorded date ≠ fetch date.
- **B.3:** Rate from FRED DTB3 (discount → continuous). Dividend = trailing 12m distributions / spot → continuous.
- **B.5:** `make fetch` manual/live once. Snapshot COMMITTED to `data/snapshots/` (CSV + metadata JSON + SHA256 sidecar). `make all` uses committed snapshot only — fully reproducible, offline. Live tests marked `network`, skipped by default.

## Files
- Create: `src/volsurf/market_data.py`, `src/volsurf/rates.py`, `tests/test_market_data.py`, `tests/test_rates.py`

## Interfaces
- `fetch_chain(ticker) -> (options_df, spot, fetch_time_utc)` — yfinance `Ticker.options` + `option_chain` per expiry, calls+puts concatenated.
- `risk_free_from_dtb3(discount_rate, tenor_days=91) -> float`
- `dividend_yield_continuous(trailing_12m_dividends, spot) -> float`
- `save_snapshot(options_df, meta, out_dir) -> Path` — CSV + metadata JSON + SHA256 sidecar
- `load_snapshot(path) -> (options_df, meta)` — verifies checksum; raises on mismatch

## Steps
1. **Tests first:**
   - Save→load round-trips DataFrame exactly.
   - Tamper one byte of CSV → `load_snapshot` raises.
   - Metadata contains: ticker, snapshot date, fetch time UTC, spot, rate value + source, dividend yield + method, package versions, yfinance version, row counts.
   - `risk_free_from_dtb3`: discount 0.05 @ 91d → expected continuous rate (hand-computed).
   - `fetch_chain` marked `network`; unit tests use recorded fixture.
2. **Rate conversion:** P = 1 − d·91/360; r = −ln(P)·365/91.
3. **Dividend:** q = ln(1 + y), y = trailing 12m distributions / spot. Method in metadata.
4. `fetch_chain`: record fetch time; store raw yfinance `impliedVolatility` as `yf_iv` for comparison ONLY — never in calculations.
5. Manual once: `make fetch` during/just after market hours; fill `snapshot_date` + rate in `config/market.yaml`; commit snapshot to `data/snapshots/`.
6. Verify committed snapshot reloads and checksum passes.

## Exit criteria
Unit tests green; one snapshot committed with checksum + metadata; `config/market.yaml` filled.

**Timing note:** quotes unreliable off-hours — fetch during session or immediately after close; record fetch time in metadata.
