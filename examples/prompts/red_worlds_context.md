# Red Worlds — context for AI-assisted exploration

Paste this file into your AI conversation before asking carbon modelling questions.
It gives the assistant the background it needs to answer accurately and cite the
right assumptions.

---

## What Red Worlds is

Red Worlds is an open-source Python simulation engine for **Red Carbon**, a web game
about decarbonisation. The engine takes player actions — build more wind farms, swap
gas heating for heat pumps, reduce meat consumption — and calculates the downstream
change in carbon emissions using a real global economic model.

The underlying model is **EXIOBASE 3.8.2**, a Multi-Regional Input-Output (MRIO) table
covering ~49 countries and regions, 200 product categories, and physical satellite
accounts including CO₂ and other greenhouse gases. EXIOBASE is used by academic
researchers and the IPCC; it is not a toy model.

Red Worlds extrapolates the 2011 EXIOBASE data forward to a **Baseline year of 2027**
and runs player scenarios year-by-year from there.

---

## The three player actions

Everything in the engine reduces to one of three action types:

**BUILD** — add new productive capacity (e.g. build 10 GW of offshore wind). During
the build period, capital expenditure flows into the construction sector. After
completion, the energy mix shifts: the new technology generates output and the
displaced technology contracts. CapEx is spread linearly across the build period.
All units are built in parallel (the game explores what collective action *could*
achieve, not what a single contractor could schedule).

**SWAP** — redirect a share of existing flows from one product/sector to another
(e.g. shift 20% of gas heating demand to heat pumps). The economy rebalances to keep
total expenditure conserved — money not spent on gas goes somewhere else.

**REDUCE** — genuinely consume less (e.g. reduce flying by 30%). Unlike SWAP, the
money saved is not redirected. The economy shrinks in that sector. This models
*eco-sufficiency*: choosing less, not just differently.

The key design decision: SWAP and BUILD rebalance money across the rest of the economy
(the IO system stays closed); REDUCE does not (it is a deliberate post-growth framing).

---

## How the numbers work

Red Worlds uses **input-output (IO) analysis**. The core insight: every purchase
triggers a chain of upstream production. Buying a solar panel requires steel, which
requires coal, which requires energy, which requires more steel... IO tables capture
these supply chains in a matrix called the Leontief inverse (L). Multiply L by final
demand (Y) to get total output; multiply by a satellite intensity matrix (S) to get
total emissions.

Key matrices in the model:
- **Z** — intermediate demand (what each sector buys from every other sector)
- **Y** — final demand (what households, governments, and investors buy)
- **A** — technical coefficients (Z normalised by output — the "recipe" for each sector)
- **L** — Leontief inverse: (I − A)⁻¹, the full multiplier matrix
- **F** — satellite flows (emissions in physical units, e.g. kg CO₂)
- **S** — satellite intensity (emissions per unit of output)
- **D** — total footprint (S × L × Y — the number players care about)

Player actions modify Z or Y. The engine then recalculates downstream.

---

## Scientific assumptions and simplifications

The full rationale for every design decision is in
[`docs/design/assumptions.md`](../../docs/design/assumptions.md).
When in doubt, that document is authoritative — not this file, not the AI.

Key assumptions to know:
- **Currency**: all monetary values are in **2026 constant million USD** (converted
  once from EXIOBASE's 2011 million EUR during baseline construction).
- **Prices**: engine calculations use **basic prices** (producer prices, excluding
  taxes and trade/transport margins). Player-facing costs are shown in **purchaser
  prices** (basic × 1.20 approximation for now; full TT/TTM conversion is planned).
- **7 game regions**: EXIOBASE's 49 regions are aggregated to USA & Canada, Latin
  America, Europe & Central Asia, Africa & Middle East, South Asia, Mainland East
  Asia, and South East Asia & Pacific Ocean. See `data/concordances/region_mapping.csv`.
- **Game balance comes first**: scientific accuracy matters, but the game must be fun
  and fair. BUILD, SWAP, and REDUCE are all designed to feel like viable choices.
  The reference for design decisions is *The Art of Game Design* by Jesse Schell.

Full citations for EXIOBASE and pymrio are in [`docs/references.md`](../../docs/references.md).

---

## Current implementation status

Be honest with the user about what is and isn't built yet:

| Component | Status |
|-----------|--------|
| EXIOBASE baseline data (2011 pxp) | Downloaded and extracted |
| Currency conversion (2011 MEUR → 2026 MUSD) | Implemented — `engine/currency.py` |
| Region aggregation (49 → 7 game regions) | Implemented — `engine/regions.py` |
| Basic → purchaser price conversion | Implemented — `engine/prices.py` |
| BUILD action | Stub — `actions/build.py` |
| SWAP action | Stub — `actions/swap.py` |
| REDUCE action | Stub — `actions/reduce.py` |
| Growth extrapolation (2011 → 2027+) | Stub — `jobs/apply_growth.py` |
| IO rebalancing (BUILD/SWAP) | Stub — `engine/balancing.py` |
| Scenario generation | Stub — `jobs/update_scenarios.py` |

"Stub" means the function signature and docstring exist but the body raises
`NotImplementedError`. The stubs are paired with skipped tests and GitHub issues.

---

## How to navigate the codebase

If you want to explore or discuss a specific part:

| What you're asking about | Where to look |
|--------------------------|---------------|
| Scientific rationale for any design choice | `docs/design/assumptions.md` |
| Game mechanics (what BUILD/SWAP/REDUCE do) | `docs/design/game_mechanics.md` |
| System architecture | `docs/design/architecture.md` |
| How EXIOBASE sectors map to game scenarios | `data/concordances/exiobase_to_scenario.csv` |
| How EXIOBASE regions map to game regions | `data/concordances/region_mapping.csv` |
| Engine pure functions (currency, regions, prices) | `src/redworlds/engine/` |
| Tests (fast, no EXIOBASE needed) | `tests/engine/` |
| Full citations | `docs/references.md` |

---

## Good questions to start with

- "Walk me through what happens in the IO tables when a player reduces steel demand by 10%."
- "Which EXIOBASE product categories would I need to modify to model a shift from gas heating to heat pumps in Europe?"
- "Why does Red Worlds use basic prices internally but show purchaser prices to players? What's the difference?"
- "How does the Leontief inverse work, and why does it matter for calculating emissions from a player action?"
- "If a player builds 5 GW of offshore wind in the Mainland East Asia region, which EXIOBASE sectors are affected and how?"
- "What are the known limitations of this model — what does it deliberately not capture?"

For questions about specific numbers ("how much CO₂ would X save?"), the engine needs
to be run — the AI can explain the methodology and walk through the calculation
conceptually, but actual numbers require the implemented code and real EXIOBASE data.
