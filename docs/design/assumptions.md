# Game Design Assumptions

## Overarching principles

The engine exists to serve the game, and the game exists to be fun. That priority
order matters. The reference for all game design decisions is **The Art of Game Design:
A Book of Lenses** by Jesse Schell — when a design choice is contested, this is the
common language.

**Balance is an overriding concern.** BUILD, SWAP and REDUCE should each feel like a
genuinely viable, rewarding choice, and playtesting is what measures whether they do. It is
not the first thing this engine is for — accuracy is — but it is the concern that can
override a modelling preference when the two collide. How that is handled, and what has
actually been needed so far, is in
[Keeping the wings in line](#keeping-the-wings-in-line) below.

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

For the two consumer-side SWAP tapes, one third is an **energy ratio**, never a spend ratio:
COP 3 for heat-pump heat and the same order-of-magnitude energy ratio for EV travel. Removed
fuel spend is converted to TJ at each source product's EXIOBASE basic price. One third of
those TJ is then priced from the region's existing household electricity-generation mix,
with *Distribution and trade services of electricity* added separately at its baseline
margin. The budget remainder is re-spent; when electricity plus delivery costs more than
the removed fuel, balancing withdraws the difference from the rest of household demand.

This distinction changes the EV result materially. On the 2011 Region 3 table, the removed
petrol/diesel basket averages €11.59/GJ; generation averages €30.25/GJ and its delivery
margin is almost another euro per euro of generation. Even at one third of the energy, the
electricity purchase costs more than the displaced fuel. With only the directly observed
32.9% road-transport share of household net energy used to apportion `F_Y`, the flat-rebound
MVP result is a small emissions increase. It is reported as such and marked provisional;
changing its sign requires better fuel-resolved direct emissions or a different, documented
rebound rule, not an `abs()` or a tuned efficiency.

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

*Consequence for BUILD — decided for the MVP:* endogenised capital is proportional to output, and a plant under
construction produces nothing, so the J-curve still needs an explicit capex injection in
the build years. During operation the coefficients then charge the plant's capital at the
sector's average maintenance-and-replacement rate, which overcounts a long-lived new plant
a little by applying the steady-state average from its first operating year. We deliberately
do **not** net this out: the cached `A` matrix does not retain a separable capital component,
and subtracting an invented amount would treat the new plant differently from every baseline
plant. The likely bias is roughly the construction hump spread over forty years and is small
against displacement (the nuclear construction total is 1.7% of operating abatement). Revisit
only when the baseline stores capital coefficients separately or the model gains cohorts.

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

### BUILD: operation replaces fossil electricity coefficients

After construction, the built TWh is priced from EXIOBASE's own technology row: monetary
output divided by the `Energy Carrier Supply: Total` satellite row. That amount is moved
proportionally out of coal-, gas- and oil-electricity inputs to every Region 3 industry and
final-demand column and into the built product. Every affected A or Y column keeps the same
total. The technology's existing stressor intensity is left alone, then the Leontief inverse
is rebuilt (Wiebe et al. 2018 §3.3).

Changing A is non-linear after inversion. BUILD is therefore solved at 0.25, 0.5, 0.75 and
1.0 deployment and the export carries all four values. The construction phase remains
linear because it changes Y only.

The EXIOBASE 2011 coefficient diagnostic requested before trusting the BUILD result gives
Region 3 lifecycle intensities of about **44 g CO₂e/kWh for nuclear, 57 for solar PV, 211
for geothermal, 669 for gas and 1,152 for coal**. Geothermal is surprisingly high, as
pymrio issue #72 warned; it is retained rather than tuned away. The table is reporting what
its geothermal sector contains. Its score is therefore exported as **provisional**, not
ready, until the coefficient can be reconciled with the technology literature.

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

The cached 2011 baseline stays one step from source, in 2011 MEUR. Player-facing BUILD
budgets are converted back through the purchaser-price markup and the 2.072 currency factor
before being injected into that table. Exported GDP impacts state the table unit explicitly.
A future walked 2050 baseline may choose to persist in 2026 MUSD, but the unit must travel
with the artifact rather than be assumed.

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

## Keeping the wings in line

<a id="keeping-the-wings-in-line"></a>

A player who finds that building always beats reducing will build every time, and the game
stops being about the choice. So the three wings are kept close enough in value that picking
one is a question about *how you want to act* rather than arithmetic.

### How it is handled: one anchor, and a spread around it

Balance here is not a per-tape dial. It is one shared anchor plus a deliberate spread.

**The anchor is the golden tape.** Every tape is normalised to the same reference value —
about one "brick", roughly 1 Gt of CO₂ cumulative over 2050–2100. A tape's cover magnitude
is then *derived* from that: ten reactors, twelve million homes, a percentage of a basket are
answers to "what equals a brick?", not numbers anyone picked. They land on unrelated-looking
figures precisely because that is what equal climate effect across unlike interventions looks
like. A shelf where every cover reaches for the same round number is the visible symptom of
the rule having been broken.

**The spread is what distinguishes tapes.** With expected value held equal, what makes one
tape different from another is the *distribution* around it — how wide the outcome band is,
how it fails, how abrasive it is civically. That is the design lever, and it is the game's to
pull. Equal expected value with unequal variance is a real choice between real strategies;
unequal expected value is just a right answer and a wrong one.

So the engine's job is to report what a tape is worth, and the anchor keeps those reports
comparable. The distribution work happens game-side and does not touch the model.

### What has actually been needed

**Nothing yet.** No tape's modelling has been adjusted for balance, and the wings have not
had to be weighted differently. Recorded here so the absence is legible: if a future reader
finds this section elaborate, it is because the *principle* was worth settling early, not
because the practice has been extensive.

When an adjustment is needed it happens **here, in the open, labelled, with the
physically-derived figure kept beside it**. The one thing that will not happen is a number
moved quietly: a ceiling changed for balance says so in its `regional_ceiling_basis`.

That record is worth keeping for its own sake. *How much* a model has to be bent to make
three climate strategies feel equally worthwhile is a real finding about those strategies,
not just about the game. If building needs no help and reducing needs a thumb on the scale,
that is telling you something about the world.

### The anchor itself is under review

Whether "the same brick" is well enough defined to carry this much weight is an open
question — three specific problems with it are set out in
[`tape_records.md` §10](tape_records.md#the-golden-tape-under-scrutiny). None of them is
fatal and none blocks the first playtest, but they bear on exactly this section, so read
them before leaning on the anchor.

### Further reading

- [*The Art of Game Design: A Book of Lenses*](https://schellgames.com/art-of-game-design),
  Jesse Schell — this project's reference for game design decisions generally. The balance
  chapter sets out twelve kinds of game balance, of which "fairness between strategies" is
  only one; worth knowing before assuming ours is the only sense meant.
- [Game Balance Concepts](https://gamebalanceconcepts.wordpress.com/2010/07/07/level-1-intro-to-game-balance/),
  Ian Schreiber — a free ten-week course, online in full, on balancing as a practical craft.
  Schreiber and Brenda Romero later wrote [*Game Balance*](https://www.routledge.com/Game-Balance/Schreiber-Romero/p/book/9781498799577)
  as the book-length version.

How this lands per tape — which ceilings were derived and which were adjusted — is in
[`tape_records.md`](tape_records.md).

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
