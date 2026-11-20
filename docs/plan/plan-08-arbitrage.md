# Task 08: American Option Quote Diagnostics

**Source:** PRD §6.6, §8.4, RQ4; implements quote-level FR-8 checks. Task 09 owns post-IV calendar diagnostics.

## Scope

Compare raw and cleaned quotes from the same checksum-verified SPY snapshot. Use snapshot spot, date, rate, and dividend yield; no live data or substituted inputs. Assume one underlying and homogeneous contracts. Require positive maturity and strike, known option side, and finite `0 < bid <= ask`. Exclude all occurrences of ambiguous duplicate `(expiry, strike, option)` keys. Adjacency uses retained strikes only.

## Checks

- **American put–call bounds:** match calls and puts by expiry and strike. With nonnegative constant `r` and `q`, compare `Cmid-Pmid` and `[Cbid-Pask, Cask-Pbid]` against `[S exp(-qT)-K, S-K exp(-rT)]`. A spread-robust flag requires disjoint intervals. Do not infer exact forwards or dividends from this band.
- **Strike monotonicity:** check neighboring retained strikes per expiry and side. Calls should not rise and puts should not fall as strike increases. A spread-robust flag requires a breach even at the most favorable bid/ask endpoints.
- **Call convexity:** compare the middle price against the strike-distance-weighted outer prices. For spread-robust flags, compare middle bid with weighted outer asks.

Use an absolute price tolerance (`1e-8` by default); boundary contact is not a breach. Flags are local diagnostics, not claims about synchronized prices or executable arbitrage. Compare rates as well as counts: cleaning changes eligibility and adjacency.

## Implementation and exit criteria

1. Test synthetic clean and violating chains, American CRR bounds, nonuniform strikes, eligibility, group isolation, and the CLI before implementing.
2. Add `run_checks(df, spot, r, q, snapshot_date, tol=1e-8)` in `src/volsurf/arbitrage.py`.
3. Add offline `python -m volsurf.cli arbitrage <snapshot.csv> [-o results]`. Write `results/arbitrage_report.csv` with stage, expiry, check, input/eligible quotes, tested comparisons, midpoint/spread-robust flags, and sample strikes. Zero tested means no evidence for that check.
4. Document assumptions in `docs/american_parity_bounds.md`. Verify deterministic output on the frozen snapshot and run offline tests and Ruff.

## Gap audit round 3 (2026-11-20) — re-check
No new gaps. Eligibility mask (`bid > 0`, `ask >= bid`, positive tte,
duplicate-key exclusion), American bounds `[S e^{-qT} − K, S − K e^{-rT}]`,
non-uniform-spacing convexity weight, and zero-tested semantics all verified
in code and tests; report committed for the frozen snapshot. Cross-module
note (owned by plan-07): `run_checks` treats crossed quotes (bid > ask) as
ineligible while `clean` lets them survive — the eligibility disagreement is
recorded in plan-07 round 3, fix there, not here. No open items.
