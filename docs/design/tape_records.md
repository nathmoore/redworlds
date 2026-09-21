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
- **Balance calls**, when a wing turns out to dominate — but see §8, because those are made
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
down as what it is — see §8.

---

## 2. Where this work sits

Getting an intervention onto a shelf runs through six phases, and **this repo owns two of
them**:

| | | |
|---|---|---|
| **Phase 0** | Is it a tape at all? | game |
| **Phase 1** | **Mechanism** — can the table express it? Which matrix, which products? | **here** |
| **Phase 2** | **Ceiling and the brick** — how much of it could a region do, and what is that worth? | **here** |
| **Phase 3–6** | Cover, who argues for it, balance, wiring | game |

The line is that **an intervention is a thing you can do to a region's economy; a tape is an
intervention someone is arguing for.** Everything about the first is checkable by a stranger
and lives here. Everything about the second is authorship and lives in the game.

Two things follow. **The engine's half comes first, because it is the half that can say no.**
An intervention EXIOBASE cannot express is not modellable at any magnitude, and a tape that
cannot reach a brick inside its physical ceiling should fail here rather than after someone
has written its argument. And **failing is a result, not a waste**: one candidate is
currently stopped at Phase 1 because the effect it claims — electricity curtailment — is not
a thing this table contains. No amount of tuning downstream fixes that, and finding it early
is the protocol earning its keep.

If you improve a basket or a ceiling here, you are doing Phase 1 or 2 work, and there is a
gate after it: every product must validate against the table, baskets must not overlap
between tapes, and the simplification must be written down rather than left implicit.

---

## 3. How to check any number here

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

## 4. The method: MacKay's, stated exactly

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

Every ceiling in §7 carries a per-person reading. Where one is missing, that is a gap.

---

## 5. Three rules a ceiling has to obey

**Every tape has one.**

This is the rule that does the most work, and the one most often argued away. It is tempting
to say a technology is "not really limited" — but a tape with no ceiling cannot be added up,
and adding them up is the point.

The question the whole exercise is aimed at is *can we solve this?*, and that is answered by
**stacking**: how many interventions can a region run at once, how far does each one go, and
does the total close the gap. It is MacKay's method exactly. He never writes "unlimited"
against a source; he writes 0.017 W/m² against geothermal and lets the number argue. A bar
with no height silently drops out of the stack, and the stack is what the reader came for.

So when a ceiling feels impossible to state, the discipline is to ask the question more
precisely rather than to skip it:

- *Fusion* is not limited by fuel or land, so the honest question is **how many could we build
  if the technology worked as well as anyone credibly hopes** — and that is the same heavy
  forging, construction and skilled-labour constraint nuclear runs into.
- *Grid upgrades* have no obvious "how many", so the question is **how much grid is there to
  upgrade** before every line worth doing has been done and the rest is diminishing returns.
  Losses have a technical floor; the gap between today and that floor is the ceiling.

Both of those are answerable. "No ceiling" almost always means the question has not been
asked sharply enough.

**A ceiling carries only what we are confident about.** A constraint you would defend to
someone who knows the sector belongs in the ceiling. Doubt about whether a technology *works*
does not — that lives in the game's outcome odds, and putting it in both places counts the
same doubt twice.

Fusion is the worked example of both rules at once, and they pull in different directions
until you separate the questions. *How many could be built if it works?* is a physical
question with a defensible answer, and it goes in the ceiling. *Will it work?* is not, and it
goes in the band. An earlier pass here concluded fusion should carry no ceiling at all — that
collapsed the two questions into one and cost the stack a bar.

> **Not the same question as "should this tape be scarce in play".** The game may gate a
> tape's availability on its ceiling, and for most tapes that ceiling is far larger than any
> playthrough reaches, so it never binds. Fusion's ceiling is real and also never binding;
> geothermal's is real and binds hard. The engine's job is to state the number either way.
>
> A large number is not a wasted one. "650 remaining" and "3 remaining" on the same shelf
> teach the difference in scale between two interventions better than any sentence could —
> which is another reason the engine should produce a number even where nothing gates on it.

**A region is treated as one actor.** Region 3 is Europe and Central Asia: dozens of
countries that do not, in reality, coordinate. The ceiling asks what the region *could* do if
mobilised, without specifying which countries cooperated or how.

That is deliberate, and it is not laziness. Working out how a continent could act together —
without getting bogged down in whose parliament votes when — is part of what the game is for.
It also keeps the modelling honest, because the alternative is a political forecast dressed
as physics, and we have no business making one.

### Ceilings that share a constraint do not stack

A caution that follows directly from taking the stack seriously. Two ceilings can each be
correct and still not be additive, because they are limited by the same thing.

Nuclear and fusion are the clear case: both are bounded by heavy forging and construction
capacity, so a region cannot have all of both. Electrifying cars and banning gas boilers are a
softer case — each is bounded by its own stock, but both land their new demand on the same
grid. A stack that adds every ceiling is an upper bound on the upper bound, and should be
read as one.

The engine states each ceiling independently, because that is what is checkable. Knowing
which of them compete is a reader's job, and this note is here so it is not forgotten.

---

## 6. Why BUILD ceilings use a ten-year push

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

## 7. The nine tapes

Solved figures come from the 2011 cached baseline. The export carries both flat and real-curve
cumulatives, plus the explicit 0.438 intensity scalar from 2011 to 2050 (§9). `ready` means
usable; `provisional` means usable for the MVP with a named material limitation and expected
revision; `held` means no score because the mechanism is unsettled.

### REDUCE — solved

| | `eca_buy_less` | `eca_extended_product_lifetimes` | `eca_remote_work_commuters` |
|---|---|---|---|
| **Basket** | 13 products: apparel, textiles, leather, furniture, office machinery, electrical machinery, radio/TV/comms, medical/precision, motor vehicles, air transport, hotels and restaurants, recreation, tobacco | 8 products: office machinery, radio/TV/comms, electrical machinery, medical/precision, furniture, textiles, apparel, leather | Motor Gasoline, Gas/Diesel Oil, the forecourt margin, and 35% of other land transport |
| **Protected** | housing, food, household energy, vehicle fuel — this is what makes the tape progressive without means-testing | — | — |
| **Cut** | flat 25% | **uneven**, `N/(life+N)` at N = 4: short-lived products 0.50, medical 0.36, white goods 0.27, furniture 0.25 | flat 11%, except public transport at 35% of that |
| **Columns** | households only | households, NPISH, government | households only |
| **Ceiling** | 25% of the basket | 4 extra years of life per product | 140 M teleworkable workers |
| **Basis** | Behavioural. The gap between Region 3 discretionary spend per head and that of the region's own lower-middle income decile — a level people in the region already live at | Physical, from replacement cycles. Adding N years removes `N/(life+N)` of annual replacement demand; four years roughly doubles a short-lived product's life and is about as far as a repair culture reaches | Dingel & Neiman (2020) and Sostero et al. (2020) both find 37% of jobs teleworkable in the US and EU; shaded to ~35% for the region's middle-income economies |
| **Cumulative, 2011 basis** | −18.6 Gt | −12.2 Gt | −4.1 Gt |
| **Cumulative, 2050 basis, real curve** | **−7.4 Gt** | **−4.9 Gt** | **−1.6 Gt** |
| **Copies** ⌊Gt⌋ | 7 | 4 | 1 |
| **Status** | ready | ready | provisional: road `F_Y` uses an energy-share proxy |

**A cross-check worth keeping.** Basket A was estimated at "~1.4% of the basket per brick"
from the literature, before the table was run. The table says **1.34%**. Two independent
routes to the same number is the strongest evidence we have that the basket is right.

**Why the lifetimes tape is the heaviest of the three per product.** Clothing and textiles
are a large share of household spend and are replaced every few years, so a repair-and-reuse
culture removes half their replacement demand. White goods last a decade and lose a quarter.
That spread is the tape's whole mechanism, and cutting all eight products by the same
percentage would have described none of them.

**Why remote work is more carbon-intense per euro than buying less:** its basket is dominated
by motor fuel. Basket A is mostly manufactured goods whose emissions sit in supply chains
abroad — and are still credited to the buyer, because all accounting here is consumption-
based. The provisional result attributes 32.9% of direct household emissions to road travel,
matching road transport's share of household net energy; energy share is not yet a fuel-
resolved GHG account.

**Where these disagree with the game's own expectations.** The game sized buy-less at ~10
copies and lifetimes at 3–5; the table says 7 and 4. Remote work was expected at ~9 and comes
out at **1**, because its ceiling is now derived from a sourced teleworkable share and direct
emissions are no longer all treated as road transport. That is the engine reporting and a
cover needing to move, which is how this is
meant to work (§1).

### BUILD and SWAP — solved, except the held grid mechanism

| Tape | Shock at one cover or full ceiling | 2050 cumulative, real curve | Ceiling / status |
|---|---|---:|---|
| `eca_nuclear` | 10 reactors, 95 TWh/yr; 10-year build | **−0.55 Gt CO₂e** | 650 reactors |
| `eca_geothermal` | 13 GW, 91 TWh/yr; 6-year build | **−0.32 Gt CO₂e** | **provisional:** 180 TWh/yr |
| `eca_fusion` | 10-plant nuclear proxy, 2× capex and 20-year build | **−0.40 Gt CO₂e** | 650 plants; shared with nuclear, not additive |
| `eca_electric_vehicle_transition` | 80% of household petrol and diesel demand | **+1.41 Gt CO₂e** | **provisional:** 320 M cars; 0 abatement copies |
| `eca_ban_gas_supply` | 90% of household mains-gas demand, including apportioned `F_Y` | **−5.91 Gt CO₂e** | **provisional:** 95 M homes |
| `eca_smart_grid` | — | — | **held:** mechanism undecided |

The BUILD construction humps are 2.20 Mt CO₂e/yr for nuclear and fusion and 3.67 Mt/yr
for geothermal on the 2011 basis. Nuclear's ten-year construction total is about 1.7% of
its operating abatement through the real curve: the expected few-percent check. Its
ten-reactor result lands at the bottom of the contract's 0.5–1.8 Gt range after the 2050
intensity scalar, so the anchor survives without tuning.

The gas result now moves 27.4% of `impacts.F_Y`, inferred from the gross 2.8 t/home physical
anchor and the baseline direct-household total, rather than moving all household combustion.
That removes the known upper-bound error but remains a proxy, so the score is provisional.

The EV sign is a result, not a target. Removed petrol/diesel averages €11.59/GJ in the table;
household generation averages €30.25/GJ and delivery nearly doubles that spend. One third of
the energy therefore costs more than the fuel it replaces, so balancing withdraws money from
the rest of consumption. With road transport represented by 32.9% of direct-household energy,
the model's grid and rebound effects slightly exceed tailpipe savings. A better fuel-resolved
`F_Y` share may change the sign; until then the table exposes the backfire and awards zero
copies rather than taking its absolute value.

Geothermal carries a separate warning: EXIOBASE reports about 211 g CO₂e/kWh lifecycle in
Region 3, far above the usual technology literature and the 44 g/kWh table result for
nuclear. The engine retains the coefficient and marks the result provisional. See the
diagnostic in `assumptions.md`.

---

## 8. Balance, and why we do it in the open

Every tape is normalised to roughly the same value — about one "brick", 1 Gt of CO₂ — so that
building, swapping and reducing all feel like real choices. Honest modelling does not
cooperate: run the numbers straight and some tapes come out several times others.

When that happens the game designer adjusts something — a ceiling, a cover magnitude, a
mechanism — and it happens here, in public, labelled, with the physically-derived figure kept
beside it. **The one thing we will not do is adjust a number quietly.** A ceiling changed for
balance says so in its `regional_ceiling_basis`.

Why that record is worth keeping, and the game-design reading behind the target, is in
[`assumptions.md` § Keeping the wings in line](assumptions.md#keeping-the-wings-in-line).

---

## 9. What every number here is still missing

**The 2011 → 2050 intensity correction.** These are 2011 intensities. A euro removed in 2011
carries more carbon than the same euro removed in 2050 will, because the grid gets cleaner.
[`engine/intensity.py`](../../src/redworlds/engine/intensity.py) corrects for it in two
stages — an **observed** 2011 → 2026 factor of 0.73, from the ~2.1%/yr fall in the carbon
intensity of world output, and a **scenario** 2026 → 2050 factor of 0.60 continuing that rate.
The first is checkable against published data and the second is not, which is exactly why
they are separate numbers.

Neither is the real answer, which is to walk the table forward year by year. Both scale every
tape equally, so they cannot make one tape look better than another — that is what makes
shipping them safe while the walk is built, and it is the test for whether any simplification
here is shippable.

**Money.** All monetary figures are 2011 basic-price million EUR, EXIOBASE's own units. See
[`units_and_currency.md`](units_and_currency.md) for the chain to 2026 dollars.

**Where a contributor would help most, in order:** the intensity correction (§9), replacing
the provisional energy/anchor shares with fuel-resolved direct household GHG, and Region 3's
population and workforce, which several ceilings scale by and which
are currently round numbers. All three are in [`../backlog.md`](../backlog.md) with what
"done" looks like.

---

<a id="the-golden-tape-under-scrutiny"></a>

## 10. The golden tape, under scrutiny

Every tape is normalised to the same reference value — about one "brick", roughly 1 Gt of
CO₂ over 2050–2100 — and its cover magnitude is derived from that. The anchor is what makes
ten reactors comparable to a percentage of a shopping basket, so a great deal rests on "the
same brick" being a well-defined quantity.

Now that there are real numbers to test it against, three things about it need sharpening.
None is fatal, none blocks a first playtest, and all three are cheap to fix. They are here
rather than in a backlog because anyone reasoning about balance needs to know them.

### 10.1 "The brick reading" and "copies" are separated in the export

The export now gives the intervention's real-curve cumulative separately from `copies`.
For Y-side tapes the solve is at the physical ceiling. For BUILD the solve is at one cover,
then `regional_ceiling_scale` converts that cover to the physical ceiling (650 / 10 for
nuclear and fusion, 180 / 91 for geothermal). `copies` is the whole number of positive 1 Gt
abatement bricks the full ceiling delivers after the 2050 intensity scalar. A backfire
produces zero, never a positive count through an absolute value. Its exact formula travels
beside it as `copies_basis`.

One issue remains: several inherited **cover magnitudes** do not yet equal one curve-corrected
brick. The export makes that mismatch visible rather than using `copies` to hide it. Moving a
cover is game-side calibration after these engine numbers land, not a modelling adjustment.

### 10.2 Sizing on a flat curve systematically favours REDUCE over BUILD

This was the one with teeth. Legacy covers were sized on `cumulative_full_flat` — fully
deployed from 2050. Scores use the real deployment curves, which differ sharply by wing:
consumption changes ramp in over about ten years, while a BUILD tape contributes nothing
until its plants are finished and then ramps over five more.

Delivered cumulative, as a fraction of the flat figure each tape is sized on:

| Curve | Fraction of flat |
|---|---|
| Flat — what covers are sized on | 1.000 |
| REDUCE / SWAP, full by year 10 | 0.912 |
| BUILD, 10 build years | **0.765** |
| BUILD, 20 build years (fusion) | **0.569** |

The real solve confirms the arithmetic: nuclear's construction hump is 1.7% of its
curve-delivered operating abatement, and its ten-year operating curve delivers 0.765 of the
flat figure. **A BUILD tape therefore delivers about 16% less than a REDUCE tape sized to the
same flat brick**, and a 20-year build about 43% less.

The export now carries both flat and curve-corrected cumulatives and computes `copies` from
the latter, so the bias is no longer invisible. The legacy cover magnitudes still need game
calibration against those curve-corrected values; no physical ceiling was changed to make a
wing look better.

The fix is to size covers on the curve the tape will actually run, not the flat one. The flat
figure stays useful as a wing-neutral comparison, and should be labelled as that rather than
as the sizing quantity.

### 9.3 A brick of CO₂e is not a brick of warming, and the gap varies by tape

The brick is denominated in CO₂**e** — all greenhouse gases on a GWP100 basis. The game
converts cumulative emissions into a 2100 temperature reading, and that conversion (the
transient climate response to cumulative emissions) is defined on **CO₂ alone**. CO₂e and
warming are therefore not interchangeable, and the ratio between them is a property of what a
tape cuts:

| Tape | CO₂e | CO₂ | CO₂ share |
|---|---|---|---|
| `eca_remote_work_commuters` | −158.9 Mt/yr | −139.8 Mt/yr | **88.0%** |
| `eca_buy_less` | −364.8 Mt/yr | −294.8 Mt/yr | 80.8% |
| `eca_extended_product_lifetimes` | −238.4 Mt/yr | −189.9 Mt/yr | 79.6% |
| *world total, for reference* | *44.5 Gt* | *32.5 Gt* | *73%* |

The spread is about eight percentage points across three tapes — so **two tapes worth the
same brick of CO₂e differ by roughly a tenth in their effect on 2100 temperature.** A fuel
tape is nearly pure CO₂; a manufactured-goods tape carries more methane and nitrous oxide
from farming and industry in its supply chains.

A tenth is small enough not to break anything and large enough to be worth a decision:
either the brick is defined on CO₂ and the anchor becomes a warming anchor, or it stays on
CO₂e and the game accepts that equal bricks are not quite equal degrees. Carrying both
figures per tape is already decided, so the data will be there either way — what is missing
is a statement of which one the anchor *is*.

### A smaller one, noted for completeness

Deltas are world totals, not regional. For a consumption-based REDUCE tape acting on
Region 3, the two coincide almost exactly — that is consumption-based accounting working. For
a BUILD tape that changes Region 3's electricity recipe, they may not, because output shifts
across borders. Worth checking when T6 lands rather than assuming the REDUCE result carries
over.
