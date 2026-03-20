# Game Design Assumptions

## Overarching principles

The engine exists to serve the game, and the game exists to be fun. That priority
order matters. The reference for all game design decisions is **The Art of Game Design:
A Book of Lenses** by Jesse Schell — when a design choice is contested, this is the
common language.

**Balance comes first.** BUILD, SWAP, and REDUCE must all be balanced to feel like genuinely viable,
rewarding choices. We achieve this through
playtesting and iteration. The interesting question
the balancing process will surface is *how much adjustment each choice needs, and why*:
it might turn out to say something real about the relative tractability of different
climate strategies in the actual world.

**Accuracy serves clarity.** The engine should be as scientifically grounded as
possible, but not at the cost of the player losing the thread of what their choices
mean. A simplification that makes the game more legible without being misleading is
usually the right call.

The specific choices below are all deliberate. If you think one should be revisited,
raise a GitHub issue — that's exactly what the open-source model is for.

---

## Economic model

### Rebalancing: what happens to money after a player action

Three action types, three different assumptions about money:

**BUILD and SWAP** represent *substitution* — the player is spending or redirecting money,
not eliminating it. After either action, money flows are rebalanced across the rest of the
economy to keep the IO system closed. This reflects the standard MRIO assumption that
expenditure is conserved: if you spend less on gas heating, that money goes somewhere else.

**REDUCE** is different by design. It represents *eco-sufficiency* — genuinely consuming
less, not spending the savings elsewhere. The economy shrinks in that sector. This is a
deliberate post-growth framing: we want the game to explore what it means to genuinely
reduce demand, not just shift it. Whether this is the right model for all REDUCE scenarios
is a reasonable question — raise an issue if you want to discuss it.

The specific rebalancing methodology for BUILD and SWAP is not yet implemented.
See `engine/balancing.py` and GitHub issue #10.

---

### BUILD: CapEx is spread linearly over the build period

When a player builds new capacity, the capital expenditure is distributed evenly across
the build period — the same amount per simulation year, from start to finish. In reality,
spending profiles tend to be front-loaded. This simplification trades realism for
predictability: the player can clearly see what each year of the build costs. It may be
revisited once the engine is further along.

*Effect in the model:* IO construction sector spending increases by `budget / build_years`
per simulation year during the build period.

---

### BUILD: all units are built in parallel

The build period is the same whether the player builds one wind farm or a hundred — all
units are assumed to be constructed simultaneously by a large coordinated workforce.
This is intentional: the game is exploring what collective action *could* achieve, and
we don't want large ambitions to feel mechanically punishing just because the numbers
are bigger. Larger targets do carry a higher chance of cost and time overrun, but that's
handled on the Decarbonator Deck, not in this engine.

---

### Regions are amalgamated into 7 game regions

EXIOBASE covers ~49 countries and regions. Red Worlds maps these into 7 amalgamated
game regions:

| ID | Name |
|----|------|
| 1 | USA and Canada |
| 2 | Latin America and the Caribbean |
| 3 | Europe and Central Asia |
| 4 | Africa and Middle East |
| 5 | South Asia |
| 6 | Mainland East Asia |
| 7 | South East Asia and Pacific Ocean |

The exact mapping is in `data/concordances/region_mapping.csv`. Aggregation is
performed by `engine/regions.py` using pymrio's `aggregate()` method.

The rationale is legibility: the game is designed for a general audience, and country-level
granularity would make scenarios harder to relate to. Actions apply to all EXIOBASE regions
within a game region, aggregated proportionally. Results will differ slightly from running
EXIOBASE at full country resolution.

---

## IO / pymrio model

### Actions target different IO matrices — and that matters for performance

Each action type modifies a different part of the underlying IO system, which has real
consequences for how much recalculation is required:

- **REDUCE** and **Y-side SWAP** modify the final demand matrix (Y). Recalculating from
  here is relatively straightforward: update total output `x = L·y`, then recalculate
  the satellite accounts (S, M, D).
- **Z-side SWAP**, **BUILD (construction phase)**, and **BUILD (post-build energy mix
  change)** modify the intermediate demand matrix (Z) or the technical coefficients (A).
  This requires a full Leontief recalculation — recomputing A, then L = (I − A)⁻¹, then
  the full downstream chain. Significantly more expensive.

In practice this means the engine should not blindly call `calc_all()` after every change.
Functions in `engine/io_tables.py` should return enough information for the caller to
choose the minimal recalculation path.

*The exact matrix targets for each action type are a working hypothesis — they should be
verified against the pymrio documentation and EXIOBASE structure during implementation.*

---

### Basic prices vs purchaser prices

EXIOBASE records all monetary values in **basic prices**: what the producer receives,
excluding taxes on products and trade and transport margins. When a player budgets
a BUILD project, they are thinking in **purchaser prices** — the full cost to the buyer,
including taxes, trade margins, and transport.

```
Purchaser price = Basic price + Taxes on products + Trade margins + Transport margins
```

The correct implementation uses EXIOBASE's `TT` (taxes and subsidies on products) and
`TTM` (trade and transport margins) matrices to convert sector-by-sector. This is the
standard approach in detailed IO modelling.

For now, `engine/prices.py` uses a **universal markup of 1.20** (20%) as an approximation.
This is in the middle of the typical range for construction and manufactured goods
(1.15–1.25 for VAT/GST + trade margin + transport). Services tend to be lower; tax-heavy
energy products can be much higher. The simplification is acceptable for early-stage
balancing; the TODO for proper TT/TTM conversion is tracked in GitHub issue #N.

Player-facing prices in BUILD, SWAP, and REDUCE should always be quoted in purchaser
prices. Internal engine calculations use basic prices throughout.

---

### Product-by-product (pxp) IO table

Red Worlds uses EXIOBASE 3.8.2's **product-by-product (pxp)** monetary table
(`IOT_2011_pxp.zip`). The 2011 year is the latest in 3.8.2 with complete,
non-extrapolated supply-use data. Red Worlds extrapolates from 2011 to reach
the in-game **Baseline year of 2027** (one full year ahead of the current year),
and continues year-by-year from there.

The pxp table is preferred over the industry-by-industry (ixi) alternative because
product-level classification maps more naturally to the player actions (building a
technology, swapping a consumer product) and to the scenario categories in
`data/concordances/exiobase_to_scenario.csv`.

### Monetary units and currency conversion

EXIOBASE monetary values are in **2011 million EUR at basic prices**. Basic prices
are producer prices — what the seller receives — excluding taxes on products and
trade/transport margins.

Red Worlds converts all monetary values to **2026 constant million USD** before
exposing them to players. The conversion uses:
- The average 2011 EUR/USD exchange rate (ECB): **1.3917**
- The US BLS CPI-U deflator ratio 2026/2011: **≈ 1.489**
- Combined factor: **≈ 2.072** (1 MEUR 2011 ≈ 2.07 MUSD 2026)

This conversion is applied **once, during baseline construction** — the pipeline
that transforms raw 2011 EXIOBASE into the stored `BASELINE_2027` world. After
that step, all IO tables on disk are natively in 2026 constant USD. No per-action
or per-player conversion is needed.

Satellite accounts (physical units, e.g. kg CO2) are not scaled. Total emissions
(D = M × Y) are scale-invariant and remain correct.

---

## Scenario model

### Baseline year is 2027, extrapolated from 2011 EXIOBASE data

The in-game starting point — the Baseline — is **2027**, one full year ahead of the
current in-game year. We reach 2027 by applying growth extrapolation to the 2011
EXIOBASE tables. The overnight `apply_growth` job continues this year-by-year for
every simulation year that follows.

### Economic growth projections are not yet implemented

The overnight `apply_growth` job will eventually use external projections (e.g. from the
IEA or World Bank) or a simplified endogenous model to advance each player's world by one
simulation year. For now, it is a stub. See GitHub issue #5 for the planned approach.

---

## Known limitations

Every model has boundaries. Here are the main things this engine deliberately does not
(yet) capture:

- Physical energy constraints: capacity factors, grid balancing, curtailment
- Technology learning curves and cost reductions over time
- International trade effects from large regional shifts
- Non-linear feedback between sectors
- Political feasibility of player choices — this is handled on the Decarbonator Deck

These are not failures of the current model; they are the next layer of depth. The engine
is designed to be extended, and the assumptions above are the natural starting points for
future contributors to challenge.
