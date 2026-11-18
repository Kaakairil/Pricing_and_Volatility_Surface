# American put–call parity bounds (Task 08 methodology)

## Why bounds, not equality

European put–call parity forces `C − P = S·e^{-qT} − K·e^{-rT}` exactly. SPY
options are American-style: early exercise makes the put leg worth at least its
undiscounted intrinsic, so the parity difference only respects bounds.
Treating European equality as the test would flag nearly every healthy
American quote as "arbitrage".

For constant nonnegative `r`, `q` (proportional dividends), an American call
and put with the same strike `K` and expiry satisfy

```
S·e^{-qT} − K  ≤  C_A − P_A  ≤  S − K·e^{-rT}
```

Derivation sketch. Lower bound: a call is worth at least `S·e^{-qT} − K`
(discounted forward intrinsic: exercise the hypothetical European equivalent
at maturity); an American put is worth at least 0, and the European-put part
of parity drops the `K·e^{-rT}` discount. Upper bound: put ≥ `K − S·e^{-qT}`
(floored by its European equivalent), call ≥ 0, and the American call cannot
exceed spot. Both inequalities collapse toward European equality when `T → 0`
or when early exercise is worthless.

Valid only when `r ≥ 0` and `q ≥ 0`: with negative rates the upper bound
`S − K·e^{-rT}` can exceed `K` and the standard argument fails. Task 08
validates inputs accordingly.

## What the report compares

`run_checks(df, spot, r, q, snapshot_date)` screens three local comparisons
per expiry, on eligible quotes only — finite positive strike, finite
`0 < bid ≤ ask`, positive time to expiry, side in {call, put}, and no
ambiguous duplicate `(expiry, strike, option)` key (all duplicates of a key
are excluded, not just the extra copies).

**american_parity.** Matched call/put pairs at the same strike. Midpoint test:
`Cmid − Pmid` inside the bounds. Spread-robust test: the attainable quote
interval `[Cbid − Pask, Cask − Pbid]` must be wholly outside the bounds
beyond tolerance. A midpoint outside the bounds with a quote interval that
merely touches them is a midpoint flag only — bid/ask uncertainty can still
place the pair inside.

**call/put_monotonicity.** Adjacent sorted retained strikes per side. A call
at the lower strike is worth at least the higher one; a put the reverse.
Midpoint test compares mids directly. Spread-robust test: even the favorable
endpoints violate — `bid(K_hi) > ask(K_lo) + tol` for calls (i.e. the whole
of the higher-strike bid sits above the whole of the lower-strike ask).

**call_convexity.** For three adjacent strikes `K1 < K2 < K3`, the middle
price must not exceed the linear interpolation of the outer prices, weighted
by strike spacing:

```
w = (K3 − K2) / (K3 − K1)
V2 ≤ w·V1 + (1 − w)·V3
```

Unequal spacing is common in SPY chains ($1-wide near spot, $5-wide away),
so plain midpoints mis-flag. Spread-robust test: `bid2 > w·ask1 + (1−w)·ask3`.

Flags are counts against their denominators: `tested` = matched pairs /
adjacent pairs / consecutive triples; midpoint and spread-robust flags each
report against `tested`. `input_quotes` vs `eligible_quotes` per expiry makes
exclusions inferable. Zero tested comparisons means "not testable", not
"passed".

## What flags do not mean

- Flags are local diagnostics on one snapshot's quotes, not synchronized
  prices: bid/ask timestamps inside one chain need not coincide.
- A spread-robust flag is not an executable arbitrage: costs, borrow,
  assignment, and the possibility that the quote is simply stale are all
  unmodeled here.
- No global no-arbitrage proof: the screens are per-expiry, per-neighborhood;
  cross-expiry calendar statements belong to the post-IV diagnostic (Task 09)
  and are model-dependent.
- Tolerance `tol` (default `1e-8`) is in option-price units and exists for
  float boundary contact; touching a bound is never a flag.

## Interpreting the SPY snapshot run

`results/arbitrage_report.csv` from the committed 2026-11-16 snapshot
(41,416 raw quotes; 14,300 after cleaning):

| stage | tested | midpoint flags | spread-robust flags |
|---|---|---|---|
| raw | 16,793 | 4,061 | 2,227 |
| cleaned | 6,197 | 1,083 | 441 |

Cleaning removes ~65% of quotes and ~73% of spread-robust flags. The
dominant pattern is `american_parity` flagging at ~100% of tested pairs on
near-dated expiries (sample strikes at the deep-ITM end, e.g. 530/555/590 for
2026-11-20). The snapshot was fetched 09:27 ET, before the equity open:
quotes are wide and stale, deep-ITM calls sit near their exercise floor,
and the parity difference collapses toward the discount term the bounds
separate by cents. This is a data-quality observation about the snapshot,
not evidence of tradable mispricing. Monotonicity and convexity flags
cluster in far strikes and long expiries where spreads are widest; after
cleaning most expiries show zero monotonicity flags.
