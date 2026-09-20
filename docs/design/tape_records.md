# Tape records — every basket, assumption and magnitude, and how to argue with them

A **tape** is one intervention a player commits to in Red Carbon: build nuclear across a
continent, swap petrol cars for electric, buy less stuff. Each one is a real shock applied to
a real input-output table, and each one produces a real number — tonnes of CO₂ over
2050–2100.

This document is where those numbers come from. Every product basket, every ceiling, every
assumption, and the arithmetic in between. If a figure looks wrong to you, everything you
need to check it is here or one file away.

**The numbers below are not settled, and we would rather they were argued with than
believed.** Several are order-of-magnitude anchors we would happily lose to a better source.
Some are marked open because we know they are weak. This is the part of the project where an
economist, an energy modeller or a careful amateur with a spreadsheet can change the answer,
and the answer visibly changes the game.

---

## 1. What is open, and the short list of what is not

Almost all of it is open. The things that are not are smaller than people usually expect.

**Decided in-house, by the game designer:**

- **Which tapes ship**, and which region and day they appear on.
- **Who offers a tape** — the envoy characters, their voices, and which intervention each
  one is matched to. That is story work, and it is the one part with no modelling content.
- **Balance calls**, when a wing turns out to dominate — but see §7, because those are made
  *here*, in the open, and the record of them is one of the more interesting things this
  repo will produce.

**Everything else is open to anyone**: the product baskets, the physical ceilings and their
bases, the mechanisms, the magnitudes, the simplifications, and every solved number. You do
not need permission to check them, and a pull request that improves a ceiling with a better
source is exactly the contribution this repo is for.

Two things follow from that which are worth saying plainly. First, **the model does not know
what would be convenient**. If the numbers say a tape is feeble, that is what the table says,
and the interesting move is to find out why rather than to nudge it. Second, when the game
*does* need a number moved for balance, that is a legitimate thing to do and it gets written
down as what it is — see §7.

---

## 2. How to check any number here

Everything below is reproducible from this repo plus a free EXIOBASE download.

```bash
uv sync
cp config/config.example.toml config/config.toml   # then fill in your paths
just baseline                                       # builds and caches the 2050 world, ~4 min
just test -m integration                            # re-solves the tapes and checks them
```

The four files that hold everything:

| File | What it holds |
|---|---|
| [`data/concordances/exiobase_to_scenario.csv`](../../data/concordances/exiobase_to_scenario.csv) | Every product basket, as exact EXIOBASE labels |
| [`data/tech_choices/options.toml`](../../data/tech_choices/options.toml) | Every tape record: ceiling, basis, fractions, assumptions |
| [`src/redworlds/jobs/run_tapes.py`](../../src/redworlds/jobs/run_tapes.py) | Turns a record into a solved number |
| [`src/redworlds/actions/`](../../src/redworlds/actions/) | The three shocks: build, swap, reduce |

To solve a tape yourself, in about ten lines:

```python
import pymrio
from redworlds.jobs.run_tapes import run_ready_reduce_tapes
from redworlds.jobs.tape_records import load_scenario_concordance, load_tape_records

world = pymrio.load_all("data/worlds/baseline_2011_agg7")
for key, result in run_ready_reduce_tapes(world, load_tape_records(), load_scenario_concordance()).items():
    print(f"{key}: {result.annual_delta / 1e9:,.0f} Mt CO2e/yr")
```

Change a basket in the CSV, re-run, and see what it does. That loop is the point.

---

## 3. The method: MacKay's, stated exactly

*Sustainable Energy — Without the Hot Air* is this project's reference for sizing an
intervention. If you have not read it, the ten-page synopsis is free at
[withouthotair.com](https://www.withouthotair.com/) and is enough. Its method is three moves,
and we follow all three.

### Move 1 — Set economics and acceptability aside; compute what physics allows

MacKay, on whether Europe could run on its own renewables:

> "…if **economic constraints and public objections are set aside**, it would be possible for
> the average European energy consumption of 125 kWh/d per person to be provided from these
> country-sized renewable sources. … Such an immense panelling of the countryside … **may be
> possible according to the laws of physics**, but would the public accept and pay for such
> extreme arrangements?"

That is what a ceiling is here: what physics permits, deliberately ignoring cost and
willingness. The question he asks next — *would people accept and pay for it?* — is not
dropped. It is asked **somewhere else**: in the game, by the odds attached to an outcome and
by whether players pick the tape at all.

Keeping the two apart is the whole discipline. A ceiling that quietly discounts for public
acceptability is a forecast wearing a physicist's coat, and it double-counts a doubt that is
already being carried elsewhere. **If you see a ceiling here that has been shaded down
because "people would never accept that", it is a bug. Please say so.**

### Move 2 — A ceiling is an intensity times an extent

MacKay's signature table is power per unit area: wind 2 W/m², offshore wind 3, solar PV
5–20, geothermal 0.017. A ceiling is that intensity multiplied by how much of the resource
there is. The three kinds of tape differ only in what the intensity and the extent are:

| Kind of tape | Intensity | Extent |
|---|---|---|
| **BUILD** something | build rate per head | population × how long the push lasts |
| **SWAP** one thing for another | emissions per unit of stock | how much of the stock can convert |
| **REDUCE** consumption | demand per head | the share a society could forgo |

### Move 3 — Put everything in per-person units

This is the move that does the most work and the easiest one to skip. "650 reactors" is a
number nobody can sanity-check. **"19 kWh/d per person"** sits directly against MacKay's own
stack, where average European consumption is 125 kWh/d per person — so you can tell at a
glance whether a ceiling is sane, and whether one tape is three times another or thirty.

Every ceiling in §6 carries a per-person reading. Where one is missing, that is a gap.

---

## 4. Two rules a ceiling has to obey

**It carries only what we are confident about.** A constraint you would defend to someone who
knows the sector belongs in the ceiling. An uncertainty about whether a technology works at
all does not — that is what the game's outcome odds are for, and putting it in both places
counts the same doubt twice.

Worked example: **fusion carries no ceiling.** It is not limited by land, by materials, or by
industrial capacity in any way we could defend. What is genuinely uncertain is whether it
works at scale, and that is already the widest band of outcomes in the game. Giving it a
tight ceiling as well would be dressing a narrative intuition as a physical fact.

**A region is treated as one actor.** Region 3 is Europe and Central Asia: dozens of
countries that do not, in reality, coordinate. The ceiling asks what the region *could* do if
mobilised, without specifying which countries cooperated or how.

That is deliberate, and it is not laziness. Working out how a continent could act together —
without getting bogged down in whose parliament votes when — is part of what the game is for.
It also keeps the modelling honest, because the alternative is a political forecast dressed
as physics, and we have no business making one.

---

## 5. Why BUILD ceilings use a ten-year push

The shape of a ceiling differs by tape kind, and this is the part most easily got wrong.

| Kind | The ceiling is | Over 2050–2100 |
|---|---|---|
| **BUILD** | a **stock commissioned once**, during a mobilisation push | built, then operates for the remaining years |
| **SWAP** | a **stock converted** — cars, boilers — and thereafter maintained | converted progressively, then held |
| **REDUCE** | a **flow forgone** | sustained for the whole window |

So a BUILD ceiling is a build rate times a **ten-year mobilisation window**, not a rate
sustained for fifty years. Four reasons:

1. **The maths.** A rolling fifty-year build changes the technical coefficient matrix every
   year, making the tape a time-varying solve. The game scores from a precomputed table that
   multiplies one number by a deployment fraction, which only works if the shock's shape does
   not depend on when each cohort lands.
2. **The curve already assumes it.** Construction runs flat over the build years, then
   operation ramps over about five. That is one cohort.
3. **Comparability.** Every tape is normalised to about 1 Gt. If a BUILD cover were a
   sustained rate, its total would depend on how long you sustained it, and it would stop
   being comparable to a REDUCE tape.
4. **It is the decision a player makes.** You commit at a table. "How many can we commit to"
   is a move; "what is the regional build rate for fifty years" is a policy trajectory nobody
   decides in one go.

> **The mobilisation window is not the build time.** Build time is how long **one** plant
> takes (nuclear ~10 years, fusion ~20). The window is how long the region sustains
> **commissioning** (~10 years). France connected about four reactors a year while roughly
> six were under construction at any moment. Conflating the two double-counts.

### The BUILD anchor: France, 1980–1990

> France went from **15 to 55 reactors in commercial operation during the 1980s** — about
> **four grid connections a year, sustained for a decade**, peaking at eight in 1981, each
> reactor built in roughly six years, from a population of about 55 million.

That is the fastest nuclear buildout any country has achieved, which is exactly why it makes
a defensible ceiling rather than a plausible plan. Scaled per head to Region 3's roughly
900 million people: **~65 reactors a year, ~650 over a ten-year push.**

In MacKay's units, 650 reactors at 1.2 GW and 90% capacity factor is ~6,200 TWh/yr, which
across 900 M people is **~19 kWh/d per person** — a seventh of his European consumption
stack, and the same order as his "cover 5–10% of the country in photovoltaics" (50 kWh/d/p).
Large, clearly not absurd.

**Where we think this is weakest, and where help is welcome:** scaling a build rate by
population ignores the constraint the literature actually names, which is **heavy forging
capacity for reactor pressure vessels** — concentrated in a handful of plants worldwide.
Population scaling is fine while the tape is effectively unlimited at the scale the game
uses, but if this ceiling ever needs to bind, forging is where to look first.

---

## 6. The nine tapes

Solved figures come from the 2011 cached baseline at full ceiling with flat deployment, and
carry no 2050 intensity correction yet (§8). Items marked **open** are known-weak and are
being reconciled.

### REDUCE — solved

| | `eca_buy_less` | `eca_extended_product_lifetimes` | `eca_remote_work_commuters` |
|---|---|---|---|
| **Basket** | 13 products: apparel, textiles, leather, furniture, office machinery, electrical machinery, radio/TV/comms, medical/precision, motor vehicles, air transport, hotels and restaurants, recreation, tobacco | **open** — 4 products today (office machinery, electrical machinery, radio/TV/comms, medical/precision); should be 8, adding furniture, apparel, textiles, leather | Motor Gasoline, Gas/Diesel Oil. **open** — should widen to the forecourt margin and a public-transport share once baskets can be weighted |
| **Protected** | housing, food, household energy, vehicle fuel — this is what makes the tape progressive without means-testing | — | — |
| **Ceiling** | 25% of the basket | **open** — 50% flat today; should be `1 / (mean life + 1)` per product: devices ~25%, white goods ~8%, clothing ~20% | 140 M teleworkable workers |
| **Basis** | Behavioural. The gap between Region 3 discretionary spend per head and that of the region's own lower-middle income decile — a level people in the region already live at | Physical, from replacement cycles. Device life ~3–5 yrs, appliances 8–12; doubling either halves the annual replacement flow | Dingel & Neiman (2020) and Sostero et al. (2020) both find 37% of jobs teleworkable in the US and EU; shaded to ~35% for the region's middle-income economies |
| **→ basket fraction** | 0.25 | 0.5 | 0.11 = commuting's ~30% share of household car distance × ~35% of workers |
| **Annual** | −389 Mt CO₂e/yr | −64 Mt CO₂e/yr | −155 Mt CO₂e/yr |
| **Cumulative** | **−19.8 Gt** | **−3.3 Gt** | **−7.9 Gt** |

**A cross-check worth keeping.** Basket A was estimated at "~1.4% of the basket per brick"
from the literature, before the table was run. The table says **1.34%**. Two independent
routes to the same number is the strongest evidence we have that the basket is right.

**Why remote work is ten times more carbon-intense per euro than buying less:** its basket is
nothing but fuel burnt at home, so nearly every euro removed is combustion. Basket A is mostly
manufactured goods whose emissions sit in supply chains abroad — and are still credited to the
buyer, because all accounting here is consumption-based.

### BUILD and SWAP — not yet solved

These carry their fields so the export format is right first time, but the mechanisms that
solve them are still being built.

| Tape | Ceiling | Basis |
|---|---|---|
| `eca_nuclear` | **open** — 400 TWh/yr today; §5 argues for ~650 reactors, **19 kWh/d/p** | Industrial, not geological. Uranium and sites do not bind at this scale; concrete, forging and skilled labour do |
| `eca_geothermal` | 180 TWh/yr, **0.55 kWh/d/p** | Geological and hotspot-gated: Iceland, Larderello, western Turkey, the Caucasus. A proven-hotspot floor, with enhanced geothermal deliberately excluded — admitting EGS raises it an order of magnitude and it stops binding |
| `eca_fusion` | **open** — carries 400 TWh/yr; should carry **none** | Not ceiling-limited at all. See §4 |
| `eca_electric_vehicle_transition` | 320 M cars, **0.36 cars/person** | The regional fleet, less the share that cannot electrify this window: heavy rural use, and drivers without off-street parking where public charging is thin |
| `eca_ban_gas_supply` | 95 M homes, **~1 home per 9.5 people** | Housing stock. ~105 M homes on mains gas; ~90% can take a heat pump without a fabric upgrade the tape does not pay for |
| `eca_smart_grid` | **open** — carries 220 TWh/yr; should carry none yet | The mechanism is still being designed. Assigning a ceiling before that lands invents a limit for a shock nobody has specified |

---

## 7. Balance, and why we do it in the open

Every tape is normalised to roughly the same value — about one "brick", 1 Gt of CO₂ — so that
building, swapping and reducing all feel like real choices. Real modelling does not
cooperate: run the numbers honestly and some tapes come out three times others.

When that happens, the game designer adjusts something — a ceiling, a cover magnitude, a
mechanism — and the game gets more playable. **That adjustment happens here, in public, and
it is recorded as what it is.**

We think that record is one of the more interesting things this project will produce. *How
much* a model has to be bent to make three climate strategies feel equally worthwhile is a
real finding about those strategies. If BUILD needs no help and REDUCE needs a thumb on the
scale, that is telling you something about the world, not just about the game. Hiding the
adjustments would throw that away; keeping them visible turns a design chore into evidence.

The one thing we will not do is adjust a number quietly. A ceiling changed for balance says
so in its `regional_ceiling_basis`, and the physically-derived figure stays beside it.

---

## 8. What every number here is still missing

**The 2011 → 2050 intensity correction.** These are 2011 intensities. A euro removed in 2011
carries more carbon than the same euro removed in 2050 will, because the grid gets cleaner.
[`engine/intensity.py`](../../src/redworlds/engine/intensity.py) corrects for it in two
stages — an **observed** 2011 → 2027 factor of 0.71, from the ~2.1%/yr fall in the carbon
intensity of world output, and a **scenario** 2027 → 2050 factor of 0.62 continuing that rate.
The first is checkable against published data and the second is not, which is exactly why
they are separate numbers.

Neither is the real answer, which is to walk the table forward year by year. Both scale every
tape equally, so they cannot make one tape look better than another — that is what makes
shipping them safe while the walk is built, and it is the test for whether any simplification
here is shippable.

**Money.** All monetary figures are 2011 basic-price million EUR, EXIOBASE's own units. See
[`units_and_currency.md`](units_and_currency.md) for the chain to 2026 dollars.

**Where a contributor would help most, in order:** the intensity correction (§8), weighted
baskets so the lifetimes tape can use real replacement rates (§6), and Region 3's population
and workforce, which several ceilings scale by and which are currently round numbers. All
three are in [`../backlog.md`](../backlog.md) with what "done" looks like.
