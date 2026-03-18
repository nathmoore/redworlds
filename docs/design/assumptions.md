# Game Design Assumptions

The Red Worlds engine makes a number of deliberate choices about how the economy and
emissions model behaves. These are not simplifications we haven't gotten around to fixing —
they are intentional decisions, made for specific reasons, and documented here so that
players, researchers, and contributors can understand, question, and improve them.

If you think an assumption should be revisited, please raise a GitHub issue. The whole
point of open-sourcing the engine is to invite exactly that conversation.

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

### Regions are amalgamated into approximately 6 game regions

EXIOBASE covers ~49 countries and regions. Red Worlds maps these into roughly 6
amalgamated game regions (e.g. *Europe and Central Asia*, *East Asia and Pacific*).
The exact mapping is in `data/concordances/region_mapping.csv`.

The rationale is legibility: the game is designed for a general audience, and country-level
granularity would make scenarios harder to relate to. Actions apply to all EXIOBASE regions
within a game region, aggregated proportionally.

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

### Monetary IO layer (ixi), not physical layer (pxp)

Scenarios are mapped to EXIOBASE's monetary sector table (industry-by-industry, ixi)
rather than the physical layer (pxp). The monetary layer is more complete across regions
and easier to work with at this stage of the project. Integrating the physical layer —
which would allow more precise energy flow modelling — is a reasonable future improvement.

---

## Scenario model

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
