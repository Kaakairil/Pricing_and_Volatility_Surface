# PRD: Options Pricing and Implied Volatility Surface

**Project codename:** VolSurf
**Author:** Kairill
**Status:** Draft v1.0
**Last updated:** 2026-11-14
**Estimated duration:** 6 weeks (part-time, ~10 hours/week)

---

## 1. Overview

VolSurf is a from-scratch options pricing library and implied volatility analysis tool. It prices European and American options with several independent methods, backs out implied volatility from observed market prices, and builds a volatility surface (implied volatility as a function of strike and maturity) from real option chain data.

The project demonstrates three things a quantitative firm looks for: the mathematics behind derivative pricing, the numerical discipline to verify it against independent methods, and the ability to handle messy real market data. Every pricing function is cross-checked against at least one other method, and every claim in the write-up is backed by a test or a figure.

The deliverable is a Python package, a set of notebooks and figures, and a written report that a reviewer can read in about 15 minutes and reproduce in under an hour.

---

## 2. Problem Statement

Options prices encode the market's expectations about future volatility, but the relationship is not flat. Implied volatility varies with strike (the "smile" or "skew") and with maturity (the "term structure"). Together these form the volatility surface, which traders use to price, hedge, and detect mispricings.

Building this from scratch requires solving several problems:

1. Pricing a European option in closed form and checking it against simulation.
2. Pricing an American option, which has no closed form, and handling early exercise.
3. Inverting the pricing formula to recover implied volatility, which requires a numerical root finder that is stable across deep in-the-money and out-of-the-money strikes.
4. Turning noisy, incomplete real option quotes into a clean surface, and detecting when the surface violates no-arbitrage conditions.

The project answers these questions:

- **RQ1.** Do closed-form, binomial, and Monte Carlo prices agree within their theoretical tolerances across a grid of parameters?
- **RQ2.** How large is the early-exercise premium for American options on the chosen underlying, and does it match theory?
- **RQ3.** What does the implied volatility surface look like for the chosen underlying on a given date, and does it show the expected skew and term structure?
- **RQ4.** How often do raw market quotes violate basic no-arbitrage checks (put-call parity, monotonicity, butterfly spread), and how much do cleaning rules change the surface?

---

## 3. Goals

- **G1.** Implement Black-Scholes-Merton pricing, Greeks, and implied volatility inversion with documented numerical methods.
- **G2.** Implement a binomial (Cox-Ross-Rubinstein) pricer for American options and a Monte Carlo pricer with variance reduction.
- **G3.** Verify all pricers against each other and against known analytical benchmarks, with stated tolerances.
- **G4.** Fetch, snapshot, clean, and store real option chain data for one liquid underlying.
- **G5.** Build an implied volatility surface with interpolation and visualize it as a smile, term structure, and 3D surface.
- **G6.** Run and report the no-arbitrage checks on the cleaned data.
- **G7.** Deliver a reproducible repository where one command regenerates all figures and tests pass from a clean clone.

## 4. Non-Goals

- Building a trading strategy or claiming any profitability from mispricing signals.
- Real-time streaming data or execution.
- Exotic derivatives (barriers, Asians, lookbacks, variance swaps).
- Full stochastic volatility calibration (Heston, SABR). Listed as an optional stretch goal.
- Fixed income, credit, or non-equity underlyings.
- Institutional-grade data quality. The project works with free data and documents its limitations.

---

## 5. Target Audience

- **Primary:** Technical reviewers and recruiters at quantitative trading and derivatives firms, who will evaluate mathematical rigor, numerical care, and code quality.
- **Secondary:** Me, as a reference for interview discussions on derivatives pricing.
- **Tertiary:** Students learning derivatives who want a verified, readable reference implementation.

---

## 6. Product Scope

### 6.1 Pricing Engine

| Method | Options supported | Purpose |
|---|---|---|
| Black-Scholes-Merton (closed form) | European calls and puts, with continuous dividend yield | Benchmark and fast pricing |
| Cox-Ross-Rubinstein binomial tree | European and American calls and puts | American pricing and cross-check |
| Monte Carlo (geometric Brownian motion) | European calls and puts | Independent cross-check with variance reduction |

Monte Carlo variance reduction: antithetic variates and control variates using the closed-form price as the control.

### 6.2 Greeks

Analytical Greeks for Black-Scholes (delta, gamma, vega, theta, rho). Every analytical Greek is verified against a central finite-difference approximation of the price.

### 6.3 Implied Volatility

- Inversion of the Black-Scholes price using a bracketed root finder (Brent's method) as the primary solver.
- Newton's method with vega as a secondary solver, used only when a bracket is available and convergence is confirmed.
- Explicit handling of prices outside the no-arbitrage bounds (return NaN with a reason code, never a fabricated value).

### 6.4 Market Data

- Underlying: SPY (decided; see Section 16). Liquid, ETF with dividends and American-style exercise.
- Option chains: fetched via `yfinance` for all listed expirations and strikes, on a single fixed snapshot date.
- Spot price, dividend yield, and risk-free rate are recorded alongside each snapshot.
- Risk-free rate: a single constant in `config/market.yaml`, set from the 3-month Treasury bill rate on the snapshot date, with the source and date recorded. A ±100 basis point sensitivity check is reported.
- Each snapshot is saved with a timestamp and SHA256 checksum, following the CalibMiss data convention.

### 6.5 Data Cleaning Rules

Applied in order, with each rule's removal count recorded:

1. Drop options with zero bid or zero ask.
2. Drop options with bid-ask spread wider than a configured fraction of the mid (default 50%).
3. Use the bid-ask midpoint as the reference price.
4. Drop options with open interest or volume below a configured threshold.
5. Drop options with time to expiry below a configured minimum (default 7 days) to avoid expiry-day noise.
6. Restrict to a moneyness band (default 0.7 to 1.3 of spot in strike terms) for surface fitting.

### 6.6 No-Arbitrage Checks

Run on the cleaned data, with violation counts reported:

- **Put-call parity:** C - P should equal S e^{-qT} - K e^{-rT}, within a tolerance set by the bid-ask spread.
- **Monotonicity in strike:** call prices decrease in strike; put prices increase in strike.
- **Convexity in strike (butterfly):** call prices are convex in strike.
- **Calendar monotonicity:** total variance (IV squared times T) is non-decreasing in maturity at fixed moneyness.

### 6.7 Volatility Surface

- Interpolate implied volatility over (log-moneyness, time to expiry) using a smooth method (cubic spline or a linear interpolator on a grid, with the method documented).
- Optional stretch goal: fit an SVI parameterization slice by slice and check that the fitted slices are free of butterfly arbitrage.
- Outputs: smile plots for selected expiries, term structure at fixed moneyness, and a 3D surface plot.

---

## 7. Functional Requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-1 | Price European options with Black-Scholes-Merton including continuous dividend yield | Must |
| FR-2 | Compute analytical Greeks and verify them against finite differences | Must |
| FR-3 | Price American options with a CRR binomial tree, with convergence as steps increase | Must |
| FR-4 | Price European options with Monte Carlo, with antithetic and control variates, reporting standard errors | Must |
| FR-5 | Invert Black-Scholes to implied volatility with Brent's method, with explicit no-arbitrage bound checks | Must |
| FR-6 | Fetch and snapshot option chains with checksums and provenance metadata | Must |
| FR-7 | Apply configurable cleaning rules and log each removal count | Must |
| FR-8 | Run the no-arbitrage checks and produce a violation report | Must |
| FR-9 | Build and visualize the implied volatility surface | Must |
| FR-10 | Fit an SVI slice parameterization and check butterfly arbitrage | Could (stretch) |
| FR-11 | Calibrate Heston model to the surface | Could (stretch) |
| FR-12 | Interactive surface visualization in a notebook | Could (stretch) |

---

## 8. Verification Plan

Verification is the core of this project. Each requirement has a stated tolerance and a test.

### 8.1 Pricer Agreement

- Black-Scholes vs. binomial (European, large step count): absolute error below 0.01 for a grid of spot, strike, maturity, volatility, and rate values.
- Black-Scholes vs. Monte Carlo (European): the closed-form price lies within 3 standard errors of the Monte Carlo estimate.
- Binomial vs. Monte Carlo (European): agreement within combined tolerances.
- Binomial convergence: error for American options decreases as the number of steps grows, and the error at 1,000 steps is below 0.005 when compared to a reference value computed at 10,000 steps.

### 8.2 Analytical Identities

- Put-call parity holds to machine precision for model prices.
- Greeks match central finite differences with relative error below 1e-4 for a grid of parameters.
- Call price decreases in strike and increases in volatility and maturity (for European options with no dividends, for example).

### 8.3 Implied Volatility Round-Trip

- For a grid of volatilities and strikes, price with Black-Scholes, invert, and recover the original volatility to within 1e-6.
- Prices below intrinsic value or above the upper bound return NaN with a reason code.
- Near-expiry and deep out-of-the-money cases are included explicitly in the test grid.

### 8.4 Market Data Checks

- Each snapshot passes checksum verification on reload.
- Cleaning counts reconcile: raw count minus removed counts equals cleaned count, for every rule.
- No-arbitrage violation counts are reported before and after cleaning.

### 8.5 Known Benchmark

Where a published benchmark is available for a parameter set (for example, a textbook example in a derivatives reference), the package reproduces it and the test cites the source.

---

## 9. Experimental Design

### 9.1 Pricing Experiments

- Parameter grid: spot in {90, 100, 110}, strike at moneyness {0.8, 0.9, 1.0, 1.1, 1.2}, maturity in {1 week, 1 month, 3 months, 1 year}, volatility in {10%, 20%, 40%}, rate and dividend yield fixed at documented values.
- For each grid point, record prices from all methods, errors against the reference, and runtime.
- Monte Carlo experiments repeated across at least 10 random seeds to estimate the variance of the estimator.

### 9.2 Early-Exercise Premium (RQ2)

For American and European options on the same underlying with identical parameters, compute the premium as the difference in binomial prices. Report it by moneyness and maturity. Check the expected pattern: premium rises with rate for puts and is zero for calls on non-dividend-paying stocks.

### 9.3 Market Surface (RQ3, RQ4)

- Single snapshot date for the main analysis. Optional: daily snapshots over at least two weeks to show how the surface moves.
- Compare the surface before and after cleaning.
- Report the observed skew (IV difference between low and high strikes at a fixed expiry) and term structure at fixed moneyness.

---

## 10. Non-Functional Requirements

- **Reproducibility:** A fresh clone plus `make all` regenerates all figures and the market snapshot used in the report. Data download date, package versions, and random seeds are recorded.
- **Performance:** The full pricing verification suite completes in under 5 minutes. A single surface build completes in under 2 minutes.
- **Environment:** Python 3.11 or later. Dependencies pinned in `pyproject.toml` or `requirements.txt`.
- **Code quality:** Type hints on public functions, docstrings, `ruff` for linting, `pytest` for tests, at least 85% test coverage on the pricing and implied volatility modules.
- **Numerical safety:** No function returns NaN silently. Every failure has a reason code. Inputs are validated (positive spot, strike, and maturity; volatility in a plausible range).
- **Documentation:** Each pricing method has a short derivation note in `docs/` with equations and references.

---

## 11. Proposed Repository Structure

```
volsurf/
├── README.md
├── PRD.md
├── Makefile
├── pyproject.toml
├── config/
│   ├── market.yaml          (underlying, rate, dividend yield, snapshot rules)
│   ├── cleaning.yaml        (cleaning thresholds)
│   └── pricing_grid.yaml    (verification grid)
├── data/
│   ├── raw/                 (gitignored, checksummed snapshots)
│   └── processed/           (gitignored)
├── src/volsurf/
│   ├── bsm.py               (Black-Scholes-Merton price and Greeks)
│   ├── binomial.py          (CRR binomial tree, European and American)
│   ├── montecarlo.py        (GBM simulation, antithetic and control variates)
│   ├── implied_vol.py       (Brent and Newton solvers, bound checks)
│   ├── market_data.py       (yfinance fetch, snapshot, checksum)
│   ├── cleaning.py          (cleaning rules with removal logs)
│   ├── arbitrage.py         (no-arbitrage checks and violation report)
│   ├── surface.py           (interpolation over log-moneyness and maturity)
│   ├── svi.py               (stretch: SVI fit and butterfly check)
│   └── plots.py             (smiles, term structure, 3D surface)
├── tests/
│   ├── test_bsm.py
│   ├── test_greeks_finite_difference.py
│   ├── test_binomial_convergence.py
│   ├── test_montecarlo.py
│   ├── test_implied_vol_roundtrip.py
│   ├── test_put_call_parity.py
│   ├── test_cleaning_reconciliation.py
│   └── test_arbitrage_checks.py
├── notebooks/
│   └── exploration.ipynb
├── docs/
│   ├── bsm_derivation.md
│   ├── binomial_method.md
│   ├── implied_vol_method.md
│   └── surface_method.md
├── results/
│   ├── pricing_verification.csv
│   ├── early_exercise_premium.csv
│   ├── cleaning_report.csv
│   ├── arbitrage_report.csv
│   └── figures/
└── report/
    └── report.md
```

---

## 12. Deliverables

1. **Python package** `volsurf` on GitHub with the structure above.
2. **Verification report** (`results/pricing_verification.csv`) showing errors across all pricers and the implied volatility round-trip.
3. **Market snapshot** with checksum and provenance metadata, plus the cleaning and no-arbitrage reports.
4. **Figures:**
   - Pricing error heatmap across the verification grid.
   - Early-exercise premium by moneyness and maturity.
   - Implied volatility smiles for three to four expiries.
   - Term structure at fixed moneyness.
   - 3D implied volatility surface.
   - Before-and-after cleaning comparison.
5. **Written report** (6 to 10 pages): motivation, pricing methods with derivations, verification results, market surface findings, limitations.
6. **One-page summary** for non-specialist readers.

---

## 13. Milestones and Timeline

| Week | Milestone | Exit criteria |
|---|---|---|
| 1 | Setup and Black-Scholes | Repo created, BSM price and Greeks implemented, finite-difference Greek tests passing |
| 2 | Binomial and Monte Carlo | CRR binomial (European and American) and Monte Carlo with variance reduction; pricer agreement tests passing |
| 3 | Implied volatility | Brent and Newton solvers; round-trip tests across the grid including edge cases |
| 4 | Market data and cleaning | Snapshot fetched and checksummed; cleaning rules implemented with reconciliation tests |
| 5 | Surface and no-arbitrage | Arbitrage checks run; surface built and visualized; early-exercise premium analysis complete |
| 6 | Report and polish | Figures finalized, report written, README complete, repo cleaned, `make all` verified on a clean clone |

---

## 14. Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| `yfinance` option data is incomplete, delayed, or changes format | High | High | Snapshot once and checksum; document data limits; keep the data layer isolated so the source can be swapped |
| Implied volatility solver fails for deep ITM or OTM options | Medium | Medium | Bound checks before solving; explicit NaN reason codes; test edge cases explicitly |
| Bid-ask midpoints are stale or wide, distorting the surface | High | Medium | Spread filter; volume and open interest filter; before-and-after comparison in the report |
| American option pricing is slow at high step counts | Medium | Low | Vectorize the binomial tree with NumPy; cap steps in tests |
| Surface interpolation creates spurious arbitrage | Medium | Medium | Report arbitrage checks on the interpolated surface, not just raw quotes |
| Dividend and rate assumptions are inaccurate | Medium | Medium | Record assumptions in config; report sensitivity to rate and dividend yield |
| Scope creep into Heston or SABR calibration | High | Medium | Respect non-goals; stretch goals only after the core is verified |

---

## 15. Success Criteria

The project is considered successful if:

- [ ] All pricers agree with each other and with analytical benchmarks within the tolerances in Section 8.
- [ ] Implied volatility round-trips to within 1e-6 across the test grid, including edge cases.
- [ ] Every number in the report traces to a test, a generated CSV, or a figure.
- [ ] The market snapshot has a checksum and provenance record, and the cleaning counts reconcile.
- [ ] The no-arbitrage report is presented honestly, including violations that remain after cleaning.
- [ ] The report states the limitations of free data and the assumptions about rates and dividends.
- [ ] A clean clone runs `make all` successfully.

---

## 16. Decisions

| # | Question | Decision | Rationale |
|---|---|---|---|
| 1 | Underlying for option chain | **SPY** | Deepest and most liquid chain, so tight spreads and fewer cleaning removals. American-style exercise exercises the binomial pricer. Dividend yield must be recorded per snapshot, since it changes over time. |
| 2 | Risk-free rate source | **Constant in config**, taken from the 3-month Treasury bill rate on the snapshot date, with source and date recorded | Reproducible, avoids a fragile fetch dependency. A ±100 bp sensitivity check shows how much the surface depends on the rate. |
| 3 | Surface data | **Single snapshot** for the main analysis | Sufficient for RQ3 and RQ4 within the timeline. Daily snapshots are an optional Week 5 extension if time allows. |
| 4 | Stretch goal priority | **SVI first** (FR-10), Heston (FR-11) only if time remains | SVI parameterizes the same smile being built and its butterfly check ties to the no-arbitrage section. Heston needs a numerical optimizer and more time. |

Any change to these decisions after the market-data milestone (Week 4) requires re-snapshotting and re-running the analysis.

---

## 17. Appendix: Glossary

- **Black-Scholes-Merton (BSM):** Closed-form price for European options under geometric Brownian motion with constant volatility.
- **Greeks:** Sensitivities of the option price to inputs. Delta is to spot, gamma to delta, vega to volatility, theta to time, rho to the interest rate.
- **Implied volatility (IV):** The volatility that makes the BSM price equal the observed market price.
- **Volatility smile / skew:** The pattern of implied volatility across strikes at fixed maturity.
- **Term structure:** The pattern of implied volatility across maturities at fixed moneyness.
- **Moneyness:** Strike relative to spot. Log-moneyness is log(K / S) or log(K / F).
- **Put-call parity:** The no-arbitrage relation C - P = S e^{-qT} - K e^{-rT} for European options.
- **American option:** Can be exercised at any time before expiry. No closed form; priced numerically.
- **Early-exercise premium:** The extra value of an American option over its European counterpart.
- **Butterfly arbitrage:** A violation of convexity in strike for call prices, implying a negative-price payoff portfolio.
- **Calendar arbitrage:** A violation where total implied variance decreases with maturity.
- **SVI:** Stochastic Volatility Inspired parameterization of the implied variance smile for a single maturity.
- **Antithetic variates:** A Monte Carlo variance reduction that pairs each random path with its mirror image.
- **Control variate:** A Monte Carlo variance reduction that subtracts a correlated quantity with a known expectation.
