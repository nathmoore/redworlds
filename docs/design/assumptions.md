# Game Design Assumptions

## Overarching principles

The engine exists to serve the game, and the game exists to be fun. That priority
order matters. The reference for all game design decisions is **The Art of Game Design:
A Book of Lenses** by Jesse Schell — when a design choice is contested, this is the
common language.

**Balance comes first.** BUILD, SWAP, and REDUCE must all be balanced to feel like genuinely
viable, rewarding choices. We achieve this through playtesting and iteration. The
interesting question the balancing process will surface is *how much adjustment each
choice needs, and why*: it might turn out to say something real about the relative
tractability of different climate strategies in the actual world.

<a id="keeping-the-wings-in-line"></a>
### Keeping the wings in line

A player who finds that building always beats reducing will build every time, and the game
stops being about the choice. So the three wings are kept close enough in value that picking
one is a question about *how you want to act* rather than arithmetic. That is a design
target, and playtesting is what measures it — no amount of modelling can tell you whether a
choice feels worth making.

Honest modelling does not cooperate with this. Run the numbers straight and some
interventions come out several times others. Where that happens, the game designer adjusts
something — a ceiling, a cover magnitude, a mechanism — and it is done **here, in the open,
labelled, with the physically-derived figure kept beside it**.

That record is worth having for its own sake. *How much* a model has to be bent to make three
climate strategies feel equally worthwhile is a real finding about those strategies, not just
about the game. If building needs no help and reducing needs a thumb on the scale, that is
telling you something about the world. Hiding the adjustments would throw it away.

**Further reading, if you want the theory behind the target:**

- [*The Art of Game Design: A Book of Lenses*](https://schellgames.com/art-of-game-design),
  Jesse Schell — this project's reference for game design decisions generally. The balance
  chapter sets out the twelve kinds of game balance, of which "fairness between strategies"
  is only one.
- [Game Balance Concepts](https://gamebalanceconcepts.wordpress.com/2010/07/07/level-1-intro-to-game-balance/),
  Ian Schreiber — a free ten-week course, online in full, on balancing as a practical craft.
  Schreiber and Brenda Romero later wrote [*Game Balance*](https://www.routledge.com/Game-Balance/Schreiber-Romero/p/book/9781498799577)
  as the book-length version.

How this lands per tape — which ceilings were derived and which were adjusted — is in
[`tape_records.md`](tape_records.md).

**Accuracy serves clarity.** The engine should be as scientifically grounded as
possible, but not at the cost of the player losing the thread of what their choices
mean. A simplification that makes the game more legible without being misleading is
usually the right call.

The specific choices below are all deliberate and dated. Where a choice came from the
game's design rather than from the modelling literature, it says so. If you think one
should be revisited, raise a GitHub issue — that's exactly what the open-source model is
for. The full record of what the game needs from this engine is in
[`red_carbon_contract.md`](red_carbon_contract.md); open questions are in
[`../backlog.md`](../backlog.md).

---

## The world being modelled

### The in-game "now" is 2050 and every intervention is scored over 2050–2100

*Game decision, 2026-04-30.* The player acts in 2050, after the 1.5°C and 2°C carbon
budgets have expired. Each intervention (a "tape") is scored as **cumulative CO₂ abated
over 2050–2100** against a do-nothing baseline. There is no narrowing window and no
per-day time block: every tape gets the full fifty years.

*Effect in the model:* the engine needs one baseline world for 2050, a baseline emissions
trajectory 2050–2100, and for each tape the annual difference that a shock makes,
accumulated over the window through a deployment curve. Temperature is not modelled;
the game derives it from cumulative CO₂ (about 0.45 °C per 1000 Gt, Allen et al. 2022).

### The baseline is SSP2, built once from 2011 EXIOBASE data

*Decided 2026-09-16.* EXIOBASE 3.8.2 is a 2011 table. We extrapolate it to a 2050 world
along a "middle of the road" SSP2 pathway and continue to 2100, following the scenario
method of Wiebe et al. (2018) and Cap et al. (2024): exogenous population and GDP growth
drive final demand; technology change enters as coefficient changes with columns rescaled
to sum to one; stressors scale with coefficients. The baseline is a cacheable artifact
produced by `jobs/build_baseline.py`, not a per-player nightly tick. The exact
extrapolation recipe is an open backlog item.

### MVP scoring is a static comparative, one tape at a time

The first working engine is a stateless function: baseline world in, one shock applied,
one Leontief solve, annual delta multiplied through a deployment curve, fifty-year
cumulative out. This is exactly the "what if" method of Wiebe et al. (2018), and it means
a notebook can call the engine without a server, a queue or a per-player world. Results
are meaningful *relative to the baseline*, never as absolute levels; that is a property of
the method, not a bug.

Per-player persistent worlds, simultaneous tapes (whose Leontief interactions the game
treats as a feature) and the job queue are phase 2. The architecture for them is
sketched in [`architecture.md`](architecture.md).

---

## Economic model

### Where the money goes: three wings, three answers

The three action types differ in what happens to money, and that difference is a
deliberate feature of the game's design as much as a modelling choice
(*game decision, confirmed 2026-09-16*):

| Wing | What happens to the money | Rebound |
|---|---|---|
| **BUILD** | Construction capex is added to gross fixed capital formation during the build years (an *injection*; a *reallocation* flag that crowds out other investment instead is planned). After completion the electricity sector's technology mix changes. | Construction emissions are real and front-loaded: the J-curve. |
| **SWAP** | A closed-system rebalance: money not spent on the displaced product is re-spent on the replacement and the rest of the consumption basket. Total spend is preserved. | The re-spend *is* the rebound. A SWAP's benefit is partly eroded by design. |
| **REDUCE** | The reduced spend leaves the model. Total final demand falls; the economy shrinks in proportion, and the engine reports the GDP impact. | None. REDUCE gets full carbon credit and pays for it in booked GDP. |

REDUCE is the post-growth wing: genuinely consuming less, not spending the savings
elsewhere. A cut's carbon still depends on *which* demand is cut — a contraction that
falls on necessities (heating, food, fuel) removes less carbon per euro than a chosen
reduction in discretionary goods — so a REDUCE tape is defined by a basket of product
groups, not a flat percentage of everything.

The rebalancing weighting used by SWAP (and by BUILD under the reallocation flag) is a
single function with a weighting argument. The placeholder is flat proportional; the
planned upgrade is income-elasticity weighting per product (Bjelle et al. 2021; Cap et al.
2024 Eq. 1). See `engine/balancing.py`.

### Capital is endogenised in the baseline

*Decided 2026-09-16.* In a plain IO table, investment sits in its own final-demand column
and does not respond to changes in consumption: cut household demand for computers and
the computer factories' capital spending is untouched. We instead endogenise capital at
baseline construction using the method of Södersten, Wood & Hertwich (2018) and the
capital use matrices published for EXIOBASE 3.8.2 (Wood & Södersten, Zenodo record
7073276, product-by-product, CC-BY-4.0): the depreciation-based flow of capital goods into
each industry moves from the investment column into the technical coefficients, leaving
only net expansion as final demand.

*Why:* every SWAP and REDUCE tape then carries its capital consequences automatically
(less demand → less factory capital; more electricity → more grid and generation capital),
and renewables' in-window replacement cycles are captured without special-casing.
Construction remains a normal product; it also appears as an input of every
capital-using sector.

*Consequence for BUILD:* endogenised capital is proportional to output, and a plant under
construction produces nothing, so the J-curve still needs an explicit capex injection in
the build years. During operation the coefficients then charge the plant's capital at the
sector's average maintenance-and-replacement rate, which overcounts a long-lived new plant
a little. The overcount is roughly the size of the construction hump spread over forty
years, small against the displacement, and consistent with how the baseline treats every
other plant. It can be netted out of the injection later if it matters.

### BUILD: capex is spread linearly over the build period

Capital expenditure is distributed evenly across the build years. Real spending profiles
are front-loaded; the simplification trades realism for predictability. The split of
capex across EXIOBASE products (construction, machinery, electrical equipment, business
services) follows the technology-specific shares in Wood/Wiebe et al. (2018) SI Table SI1.
The carbon per euro of that spend is not an assumption: it is what the model returns for
those products in that region.

### BUILD: all units are built in parallel

The build period is the same whether the player builds one reactor or ten — all units are
assumed to be constructed simultaneously by a large coordinated workforce. The game is
exploring what collective action *could* achieve, and large ambitions should not feel
mechanically punishing just because the numbers are bigger. Overrun risk is handled by
the game's variance roll, not in this engine.

### Regions are amalgamated into 7 game regions

EXIOBASE covers 49 countries and rest-of-world blocks. Red Worlds maps these into 7
amalgamated game regions:

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
performed by `engine/regions.py` using pymrio's `aggregate()` method. Japan sits in
region 7 (the OECD-and-aspiring Pacific grouping); Taiwan sits in region 6 with China and
Korea, following the game's regions doc (settled 2026-09-17).

The rationale is legibility: the game is designed for a general audience, and
country-level granularity would make scenarios harder to relate to. Results will differ
slightly from running EXIOBASE at full country resolution.

---

## IO / pymrio model

### Actions target different IO matrices — and that matters for performance

Each action type modifies a different part of the underlying IO system:

- **REDUCE** and **Y-side SWAP** modify final demand (Y). Recalculating from here is
  cheap: total output `x = L·y`, then the satellite accounts. The Leontief inverse is
  unchanged and can be cached with the baseline.
- **BUILD (construction phase)** adds to the investment column of Y — also cheap.
- **BUILD (post-build)** and **Z-side SWAP** change technical coefficients (A) or the
  stressor matrix (S). These need a full recalculation: A, then L = (I − A)⁻¹, then the
  downstream chain. On the 9800 × 9800 EXIOBASE system that is seconds to minutes.

The engine should not blindly call `calc_all()` after every change. Functions in
`engine/io_tables.py` should return enough information for the caller to choose the
minimal recalculation path. *Y-side tapes are the MVP path for this reason.*

### Basic prices vs purchaser prices

EXIOBASE records all monetary values in **basic prices**: what the producer receives,
excluding taxes on products and trade and transport margins. When a player budgets
a BUILD project, they are thinking in **purchaser prices** — the full cost to the buyer,
including taxes, trade margins, and transport.

```
Purchaser price = Basic price + Taxes on products + Trade margins + Transport margins
```

The correct implementation uses EXIOBASE's `TT` (taxes and subsidies on products) and
`TTM` (trade and transport margins) matrices to convert sector-by-sector. For now,
`engine/prices.py` uses a **universal markup of 1.20** (20%) as an approximation, in the
middle of the typical range for construction and manufactured goods (1.15–1.25). Services
tend to be lower; tax-heavy energy products can be much higher. Proper TT/TTM conversion
is a backlog item.

Player-facing prices should always be quoted in purchaser prices. Internal engine
calculations use basic prices throughout.

### Product-by-product (pxp) IO table

Red Worlds uses EXIOBASE 3.8.2's **product-by-product (pxp)** monetary table
(`IOT_2011_pxp.zip`). The 2011 year is the latest in 3.8.2 with complete,
non-extrapolated supply-use data, and 3.8.2 is the last release under CC BY-SA 4.0. The
pxp table is preferred over industry-by-industry because product-level classification
maps more naturally to the player actions (building a technology, swapping a consumer
product) and to the scenario categories in `data/concordances/exiobase_to_scenario.csv`.
The capital use matrices are also published at pxp resolution for 2011.

### Monetary units and currency conversion

EXIOBASE monetary values are in **2011 million EUR at basic prices**. Red Worlds converts
all monetary values to **2026 constant million USD** before exposing them to players:

- The average 2011 EUR/USD exchange rate (ECB): **1.3917**
- The US BLS CPI-U deflator ratio 2026/2011: **≈ 1.489**
- Combined factor: **≈ 2.072** (1 MEUR 2011 ≈ 2.07 MUSD 2026)

This conversion is applied **once, during baseline construction**. After that step, all
IO tables on disk are natively in 2026 constant USD. Satellite accounts (physical units,
e.g. kg CO₂) are not scaled; total emissions are scale-invariant and remain correct. A
separate real-to-nominal step will be needed if the game ever shows prices in a later
year's money; the 2050 world stays in 2026 constant USD.

---

## What the game sends and what it expects back

The game's finale resolves dice, variance and civic effects itself and sends this engine a
tape id, the realised **outcome fraction** of that tape's physical ceiling, and a push
level. The tape record carries everything physical (region, product groups, ceiling,
reference cost and build time, deployment curve). The engine derives its own inputs from
those and returns the cumulative delta, the annual curve and the GDP impact. Full contract:
[`red_carbon_contract.md`](red_carbon_contract.md) §4; data shapes:
[`game_mechanics.md`](game_mechanics.md).

Every tape is pre-sized by the game to the same expected abatement ("one brick" ≈ a
10-reactor nuclear block ≈ 1 Gt CO₂ cumulative). **How much of each intervention equals a
brick is a question this engine answers**, per region; the game's current magnitudes are
placeholders until it does.

---

## Known limitations

Every model has boundaries. Here are the main things this engine deliberately does not
(yet) capture, most of them inherited from the demand-driven MRIO method itself:

- Constant trade shares: production stays where it is today, so a large regional shift
  does not move supply chains between regions.
- No price channel: any price response (for instance a vendor raising prices when volumes
  fall) is an exogenous input, never derived.
- Physical energy constraints: capacity factors, grid balancing, curtailment. EXIOBASE has
  transmission and distribution sectors whose coefficients can carry losses, but not
  curtailment.
- Technology learning curves and cost reductions over time, beyond what the SSP2 baseline
  bakes in.
- Political feasibility of player choices — this is the game's job.

These are not failures of the current model; they are the next layer of depth. The engine
is designed to be extended, and the assumptions above are the natural starting points for
future contributors to challenge.
