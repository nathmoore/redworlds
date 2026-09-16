# Red Worlds — context for AI-assisted exploration

Paste this file into your AI conversation before asking carbon modelling questions.
It gives the assistant the background it needs to answer accurately and cite the
right assumptions.

---

## What Red Worlds is

Red Worlds is an open-source Python simulation engine for **Red Carbon**, a web game
about decarbonisation. The engine takes a player's intervention — build ten reactors,
move eleven million cars to electric, cut a basket of consumption by a few percent — and
calculates the change in cumulative CO₂ emissions over 2050–2100 using a real global
economic model.

The underlying model is **EXIOBASE 3.8.2**, a Multi-Regional Input-Output (MRIO) table
covering 49 countries and regions, 200 product categories, and physical satellite
accounts including CO₂ and other greenhouse gases. EXIOBASE is used by academic
researchers and the IPCC; it is not a toy model.

The in-game "now" is **2050**. Red Worlds builds a 2050 baseline world from the 2011
EXIOBASE table along an SSP2 pathway, with capital endogenised, and scores each
intervention against that baseline over the fifty years to 2100.

---

## The three player actions

Everything in the engine reduces to one of three action types. They differ in what
happens to the money:

**BUILD** — add new productive capacity (e.g. a 10-reactor nuclear block). During the
build years, capital expenditure is injected into investment demand for construction,
machinery and electrical equipment; that emits, so the curve rises first (the "J-curve").
After completion the electricity sector's technology mix shifts and the curve bends down.

**SWAP** — redirect a share of existing demand from one product to another at the same
volume (e.g. motor fuel to electricity for cars). Total spend is preserved: the saving is
re-spent on the replacement and the rest of the basket, and that re-spend is a real,
deliberate rebound.

**REDUCE** — genuinely consume less of a defined basket of products. The money leaves the
model; the economy shrinks in proportion and the engine reports the GDP impact. No
rebound. This is a deliberate post-growth framing.

Every intervention is pre-sized by the game to the same expected abatement, "one brick",
about one gigatonne of CO₂ over the window. How much of each intervention equals a brick
in a given region is a question the engine answers.

---

## How the numbers work

Red Worlds uses **input-output (IO) analysis**. Every purchase triggers a chain of
upstream production. Buying a solar panel requires steel, which requires coal, which
requires energy, which requires more steel. IO tables capture these supply chains in a
matrix called the Leontief inverse (L). Multiply L by final demand (Y) to get total
output; multiply by a satellite intensity matrix (S) to get total emissions.

Key matrices:
- **Z** — intermediate demand (what each sector buys from every other sector)
- **Y** — final demand (households, government, investment)
- **A** — technical coefficients (Z normalised by output — the "recipe" for each sector).
  With capital endogenised, each sector's recipe also includes the capital goods it
  consumes per unit of output.
- **L** — Leontief inverse: (I − A)⁻¹, the full multiplier matrix
- **F** — satellite flows (emissions in physical units, e.g. kg CO₂)
- **S** — satellite intensity (emissions per unit of output)
- **D** — total footprint (S × L × Y — the number players care about)

A tape modifies Y (REDUCE, SWAP, BUILD construction) or A and S (BUILD after completion).
The engine recalculates downstream, takes the annual difference against the baseline,
runs it through a deployment curve, and sums the fifty years. Results are meaningful
relative to the baseline, not as absolute levels.

---

## Scientific assumptions and simplifications

The full rationale for every design decision is in
[`docs/design/assumptions.md`](../../docs/design/assumptions.md), and the record of what
the game requires is in [`docs/design/red_carbon_contract.md`](../../docs/design/red_carbon_contract.md).
When in doubt, those documents are authoritative — not this file, not the AI.

Key assumptions to know:
- **Window and score**: cumulative CO₂ 2050–2100 against an SSP2 baseline; temperature is
  derived by the game from cumulative CO₂, not modelled here.
- **Capital is endogenised** using the published capital use matrices for EXIOBASE 3.8.2.
- **Currency**: 2026 constant million USD, converted once from 2011 million EUR.
- **Prices**: basic prices internally; purchaser prices (basic × 1.20 for now) for anything
  player-facing.
- **7 game regions** aggregate EXIOBASE's 49. See `data/concordances/region_mapping.csv`.
- **Constant trade shares, no price channel**: the standard limits of a demand-driven MRIO.
- **Game balance comes first**: every wing must be a viable choice. Research informs what
  characters in the game know; it never biases the mechanics.

Full citations are in [`docs/references.md`](../../docs/references.md).

---

## Current implementation status

Be honest with the user about what is and isn't built yet:

| Component | Status |
|-----------|--------|
| EXIOBASE baseline data (2011 pxp) | Download instructions in `data/README.md` |
| Currency conversion (2011 MEUR → 2026 MUSD) | Implemented — `engine/currency.py` |
| Region aggregation (49 → 7 game regions) | Implemented — `engine/regions.py` |
| Basic → purchaser price conversion | Implemented — `engine/prices.py` |
| Shock primitives (scale, shift, emissions) | Stub — `engine/io_tables.py` |
| Capital endogenisation | Stub — `engine/capital.py` |
| Rebalancing | Stub — `engine/balancing.py` |
| Scoring (delta → curve → cumulative) | Stub — `engine/scoring.py` |
| BUILD / SWAP / REDUCE actions | Stub — `actions/` |
| 2050 baseline construction | Stub — `jobs/build_baseline.py` |

"Stub" means the function signature and docstring exist but the body raises
`NotImplementedError`. Each stub is paired with a skipped test and a backlog or issue
entry. The working backlog is [`docs/backlog.md`](../../docs/backlog.md).

---

## How to navigate the codebase

| What you're asking about | Where to look |
|--------------------------|---------------|
| What the game needs from the engine | `docs/design/red_carbon_contract.md` |
| Scientific rationale for any design choice | `docs/design/assumptions.md` |
| Data shapes in and out | `docs/design/game_mechanics.md` |
| System architecture | `docs/design/architecture.md` |
| Open modelling questions | `docs/backlog.md` |
| How EXIOBASE sectors map to game scenarios | `data/concordances/exiobase_to_scenario.csv` |
| How EXIOBASE regions map to game regions | `data/concordances/region_mapping.csv` |
| Engine pure functions | `src/redworlds/engine/` |
| Tests (fast, no EXIOBASE needed) | `tests/` |
| Full citations | `docs/references.md` |

---

## Good questions to start with

- "Walk me through what happens in the IO tables when a player cuts a basket of consumer
  goods by 1.4%, and why the money leaving the model matters."
- "Which EXIOBASE product categories would I need to modify to model eleven million cars
  moving from motor fuel to electricity in Europe, and where does the rebound show up?"
- "Why does endogenising capital change the answer for a consumer-demand tape?"
- "Why does a BUILD tape's curve rise before it falls, and what decides how big the hump is?"
- "What are the known limitations of this model — what does it deliberately not capture?"

For questions about specific numbers ("how much CO₂ would X save?"), the engine needs
to be run — the AI can explain the methodology and walk through the calculation
conceptually, but actual numbers require the implemented code and real EXIOBASE data.
