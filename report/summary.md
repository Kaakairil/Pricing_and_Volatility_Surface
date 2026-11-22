# VolSurf — plain-language summary

**What this is.** A tool that takes real SPY option prices from one trading
day and works out the *implied volatility* of every one of them — the
market's guess of how much the S&P 500 ETF will swing, extracted from
3,394 individual option contracts.

**The headline finding.** Two standard ways of extracting that volatility
gave slightly different answers: using the simple textbook (European
Black-Scholes) formula versus the American-style tree that accounts for
SPY options being exercisable any time. Across 3,394 contracts the two
disagreed by about 0.2 basis points of volatility on
average — small at-the-money, but up to 5.8 points for
deep out-of-the-money puts. **The choice of pricing model measurably
changes the volatility you read off the market**, which matters for anyone
quoting or comparing options.

**What else we checked.**
- Three independent pricing methods (a closed-form formula, a binomial
  tree, and a Monte Carlo simulation) agree with each other to within
  stated tolerances — the math is self-consistent.
- Cleaning the raw market data removed most quote-level arbitrage
  violations (see report for exact counts); the leftovers cluster in
  stale far-from-spot quotes, which is what you'd expect from real data.
- The "price of early exercise" is essentially zero for SPY calls but
  real for deep-in-the-money long-dated puts.

**What this is NOT.** Not a trading signal, not advice, and not a forecast.
It describes one day's market prices — the surface moves every day.

**Full technical report:** `report/report.md`.
