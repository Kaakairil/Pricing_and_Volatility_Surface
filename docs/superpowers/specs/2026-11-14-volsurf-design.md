# VolSurf — Design Document

**Date:** 2026-11-14
**Spec:** `PRD_volsurf.md` (v1.0)
**Codename:** VolSurf

## Intent

From-scratch options pricing library + implied-volatility analysis tool. Prices European/American options via three independent methods, inverts to implied volatility, builds a volatility surface from real SPY option-chain data, and reports no-arbitrage violations. Demonstrates math rigor, numerical cross-checking, and messy-real-data handling for quant reviewers.

## Decisions (from PRD §16)

- **Underlying:** SPY (liquid, ETF with dividends, American-style exercise).
- **Risk-free rate:** single constant in `config/market.yaml`, set from 3-month T-bill rate at snapshot date; source+date recorded; ±100bp sensitivity check.
- **Surface data:** single snapshot date for main analysis. Daily snapshots optional later.
- **Stretch:** SVI first (FR-10); Heston (FR-11) only if time remains. FR-12 optional.
- **Non-goals:** no trading strategy, no streaming, no exotics, no stochastic-vol calibration as core, no fixed income.

## Architecture

Pure-Python numerical library with NumPy vectorization. Core math modules (bsm, binomial, montecarlo, implied_vol) are dependency-free of market-data concerns; data layer (market_data, cleaning) is isolated behind config so the fetch source can be swapped. Every public function has type hints and validated inputs; failures return NaN with a reason code, never silent NaN. Verification is test-driven with stated tolerances.

## Package layout

```
volsurf/
├── README.md  PRD_volsurf.md  Makefile  pyproject.toml
├── config/            market.yaml  cleaning.yaml  pricing_grid.yaml
├── data/raw/  data/processed/     (gitignored)
├── src/volsurf/       (package modules)
├── tests/
├── notebooks/
├── docs/              (derivation notes)
├── results/           (CSVs + figures/)
└── report/
```

## Module responsibilities & interfaces

- **bsm.py** — `black_scholes(S, K, T, sigma, r, q, option='call') -> float`; Greeks `delta/gamma/vega/theta/rho(S,K,T,sigma,r,q,option)`. Validate positive S,K,T; sigma>=0.
- **binomial.py** — `binomial_price(S,K,T,sigma,r,q,option,steps,mode='european'|'american')`. CRR tree, vectorized, converges with steps.
- **montecarlo.py** — `monte_carlo_price(S,K,T,sigma,r,q,option,paths,seed,antithetic=True,control=True) -> (price, se)`. GBM, antithetic + control variates.
- **implied_vol.py** — `implied_volatility(S,K,T,market_price,r,q,option) -> (vol, reason)`. Brent primary, Newton secondary; bound-checked, NaN+reason for out-of-bounds.
- **market_data.py** — `fetch_chain(ticker, date)`, `save_snapshot(...)`, `load_snapshot(...)` with SHA256 checksum + provenance.
- **cleaning.py** — `clean(df, rules) -> (cleaned_df, removal_log)`. Rules in PRD §6.5 order, each removal count recorded.
- **arbitrage.py** — `run_checks(df) -> report`. Put-call parity, strike monotonicity, convexity/butterfly, calendar monotonicity.
- **surface.py** — `build_surface(df) -> grid`. Interpolate IV over (log-moneyness, T).
- **svi.py** — stretch: `fit_svi_slice(...)`, butterfly check.
- **plots.py** — smiles, term structure, 3D surface, error heatmap, pre/post-cleaning.

## Verification tolerances (PRD §8)

- BS vs binomial (large steps): abs error < 0.01.
- BS vs MC: within 3 SE.
- Binomial American convergence: 1000-step error < 0.005 vs 10000-step ref.
- Put-call parity to machine precision (model).
- Greeks vs central finite diff: rel error < 1e-4.
- IV round-trip: recover σ to 1e-6.

## NFR

- Python ≥3.11; deps pinned; ruff; pytest; ≥85% coverage on pricing+IV modules.
- `make all` regenerates figures+tests from clean clone; full verify < 5 min; surface build < 2 min.
- No silent NaN; every failure has a reason code.

## What's left to the builder

- Exact ND grid/interp method in `surface.py` (document choice).
- SVI optimizer details (stretch).
- Specific yfinance column handling that actual API returns.
