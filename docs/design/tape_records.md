# Tape records — what Red Worlds owns, and how each number is derived

A **tape** is one intervention a player commits to: build nuclear, swap petrol cars for
electric, buy less stuff. A **tape record** is everything physical about it, held in
[`data/tech_choices/options.toml`](../../data/tech_choices/options.toml) with its product
basket in [`data/concordances/exiobase_to_scenario.csv`](../../data/concordances/exiobase_to_scenario.csv).

This doc is the record behind the records: who owns which field, the method each ceiling is
derived by, and a per-tape table you can check the arithmetic in. If a number in
`options.toml` looks wrong, this is where to find out where it came from.

Red Carbon's own design sheets are private. Citations to them here are **provenance, not
links** — "the game's tape modelling sheet, 2026-09-18" means a dated decision exists, and
everything you need to act on it is restated below in full. Anything that needed the private
repo to make sense has been left out rather than summarised.

---

## 1. The ownership split

The division is not "engine versus game", it is **physics versus meaning**. A ceiling is a
fact about the world that a stranger with a spreadsheet could check. A cover story is a fact
about the game.

| Red Worlds owns | Red Carbon owns |
|---|---|
| The product basket: exact EXIOBASE labels, and why each is in or out | The tape's player-facing name and how it is spoken about |
| The mechanism: which matrix the shock hits and how | Which envoy offers it, and the band around the outcome |
| `regional_ceiling`, its **basis**, and its source | Whether ceilings are shown as stock, and what "out of stock" means |
| `max_reducible_fraction` / `max_replaceable_fraction` — converting a ceiling into a basket fraction | The cover *copy* ("ten new reactors across the region") |
| Every solved number: annual delta, cumulative, GDP impact | Balance targets and whether a spread of copies feels right |
| The simplifications each number rests on | Whether a tape exists at all |

**The handshake.** The game authors a cover magnitude for feel; the engine solves it and
reports what it is really worth; the cover then moves to the engine's number. Red Worlds
never adjusts a model to hit a balance target — that would make the engine's numbers
worthless as evidence. It reports, and the game re-sizes.

**`label` in `options.toml` is an engine descriptor, not the game's name for the tape.**
"Extended Product Lifetimes" describes a mechanism; what a player reads on the shelf is the
game's business and is deliberately not carried here.

---

## 2. How a ceiling is derived

A ceiling is the **theoretical maximum** of an intervention in a region — the MacKay
question, *"what if we did as much of this as is physically possible?"* It is not a forecast
and not a target. Its job is to say how many bricks' worth of a tape the region contains,
which is what makes one tape scarce and another effectively unlimited.

### The method is MacKay's, and it is worth stating exactly

*Sustainable Energy — Without the Hot Air* is this project's reference for sizing an
intervention, and its method is three moves:

**1. Set economics and acceptability aside; compute what physics allows.** MacKay's own
statement of it, on whether Europe could run on its own renewables:

> "…if **economic constraints and public objections are set aside**, it would be possible for
> the average European energy consumption of 125 kWh/d per person to be provided from these
> country-sized renewable sources. … Such an immense panelling of the countryside … **may be
> possible according to the laws of physics**, but would the public accept and pay for such
> extreme arrangements?"

That is the ceiling, precisely: what physics permits, deliberately ignoring cost and
willingness. The question he asks next — *would the public accept and pay for it?* — is not
dropped, it is **asked somewhere else**. In this game it is asked by the outcome band and by
whether players choose the tape. Keeping the two separate is the whole discipline: a ceiling
that quietly discounts for public acceptability is a forecast wearing a physicist's coat, and
it double-counts the same doubt the band is already carrying.

**2. A ceiling is an intensity times an extent.** MacKay's signature table is power per unit
area — wind 2 W/m², offshore wind 3, solar PV 5–20, geothermal 0.017 — and a ceiling is that
intensity multiplied by how much of the resource there is. The wings differ only in what the
intensity and the extent are:

| Wing | Intensity | Extent |
|---|---|---|
| BUILD | build rate per head (France: 4 reactors/yr per 55 M) | population × mobilisation window |
| SWAP | energy or emissions per unit of stock | how much of the stock can convert |
| REDUCE | demand per head | the share a society could forgo |

**3. Put everything in per-person units, so the numbers are comparable.** This is the move
that does the most work and the one easiest to skip. "650 reactors" is a number nobody can
sanity-check; **19 kWh/d per person** sits directly against MacKay's own stack, where average
European consumption is 125 kWh/d per person. A reader who knows the book can tell instantly
whether a ceiling is plausible. A reader who does not can still tell that one tape is thirty
times another. Every ceiling in §4 therefore carries a per-person reading, and where one is
missing that is a gap, not a style choice.

### Two rules

**The ceiling carries only what we are confident about.** A ceiling we would defend to
someone who knows the sector goes here. An uncertainty about whether a technology works at
all does not — that belongs in the game's outcome band, and putting it in both places
double-counts it. This is why **fusion carries no ceiling**: it is not land- or
resource-constrained, and what is genuinely uncertain about it is whether it works, which is
already the widest band in the game. *(Game decision, 2026-09-18.)*

**A region is treated as one actor.** Region 3 is Europe and Central Asia — dozens of
countries that do not, in reality, coordinate. The ceiling asks what the region *could* do
mobilised, without specifying which countries cooperated or how. That is deliberate: working
out how a continent could act together, without getting bogged down in whose parliament
votes when, is part of what the game is for. It also keeps the engine honest, because the
alternative is a political forecast dressed as physics.

### The shape of a ceiling differs by wing

This is the part most easily got wrong, and it decides how the window is modelled.

| Wing | The ceiling is | Over the window |
|---|---|---|
| **BUILD** | a **stock commissioned once**, during a mobilisation push | built, then operates for the remaining years |
| **SWAP** | a **stock converted** — cars, boilers — and thereafter maintained | converted progressively, then held |
| **REDUCE** | a **flow forgone** | sustained for the whole window |

**BUILD ceilings are a rate times a mobilisation window, not a rate sustained for fifty
years.** Four reasons, the first of which is the engine's:

1. A rolling fifty-year build makes the technical coefficient matrix change every year, so
   the tape becomes a time-varying solve. That breaks the linearity the precomputed table
   depends on — one number the game multiplies by an outcome fraction only works if the
   shock's shape does not depend on when each cohort lands. See
   [`red_carbon_contract.md`](red_carbon_contract.md) §4.4.
2. The deployment curve the game already draws assumes one cohort: construction flat over
   the build years, operating ramping over about five years, flat after.
3. The brick normalisation needs it. A brick is the cumulative of one cover over the window;
   if a cover were a sustained rate, its cumulative would depend on how long you sustain it
   and BUILD would stop being comparable to REDUCE.
4. It is the decision a player actually makes. You commit at a table. "How many can we
   commit to" is a move; "what is the regional build rate for fifty years" is not.

> **Do not confuse the mobilisation window with `build_years_reference`.** `build_years` is
> how long **one** plant takes (nuclear ~10, fusion ~20). The mobilisation window is how long
> the region sustains **commissioning** (~10 years). France connected about four reactors a
> year while roughly six were in flight at any moment. Conflating the two double-counts.

---

## 3. The BUILD rate anchor: France, 1980–1990

The citable fact underneath every BUILD ceiling.

> France went from **15 to 55 reactors in commercial operation during the 1980s** — about
> **four grid connections a year sustained for a decade**, peaking at eight in 1981, each
> reactor built in roughly six years, from a population of about 55 million.

That is the fastest nuclear buildout ever achieved, so it is a defensible ceiling rather
than a plausible plan. Scaled per head to Region 3's roughly 900 million people it gives
**~65 reactors a year, ~650 over a ten-year mobilisation** — about 65 covers of the
ten-reactor tape, which is to say nuclear is effectively ungated at any cohort size the game
will see.

**In MacKay's units:** 650 reactors at 1.2 GW and 90% capacity factor is ~6,200 TWh/yr, which
across 900 M people is **~19 kWh/d per person**. Against his European consumption stack of
125 kWh/d per person, that is a seventh of all energy from one tape's ceiling — large, clearly
not absurd, and of the same order as his "cover 5–10% of the country in photovoltaics"
(50 kWh/d/p) and "fill a sea area twice the size of Wales with offshore wind" (50 kWh/d/p).
Being able to make that comparison at a glance is the entire reason for the per-person unit.

**What per-capita scaling ignores, and would lower the number:** heavy forging capacity for
reactor pressure vessels is globally concentrated in a handful of plants, and is the
bottleneck most often named in the literature. Skilled labour and grid connection capacity
are second-order against it. If this ceiling ever needs to bind, forging capacity is where
to look first, not population.

*Region 3's population is an order-of-magnitude figure and should be firmed from the region
concordance — see [`../backlog.md`](../backlog.md).*

---

## 4. The records

Numbers marked ⚠ diverge from the game's tape modelling sheet (2026-09-18) and are being
reconciled; see §5. Solved figures are from the 2011 cached baseline at full ceiling and a
flat curve, and carry no 2050 intensity correction yet (§6).

### REDUCE — solved

| | `eca_buy_less` | `eca_extended_product_lifetimes` | `eca_remote_work_commuters` |
|---|---|---|---|
| **Basket** | Basket A, 13 products: apparel, textiles, leather, furniture, office machinery, electrical machinery, radio/TV/comms, medical/precision, motor vehicles, air transport, hotels and restaurants, recreation, tobacco | ⚠ 4 products (office machinery, electrical machinery, radio/TV/comms, medical/precision); the sheet has 8, adding furniture, apparel, textiles, leather | Motor Gasoline, Gas/Diesel Oil ⚠ the sheet also has the forecourt margin and a public-transport share |
| **Protected** | housing, food, household energy, vehicle fuel — this is what makes the tape progressive without means-testing | — | — |
| **Columns cut** | ⚠ all three consumption columns; the sheet says households only | households, NPISH, government | households only |
| **Ceiling** | 25% of the basket | ⚠ 50% uniform; the sheet wants per-product `1 / (mean life + 1)` | 140 M teleworkable workers |
| **Ceiling basis** | Behavioural. The gap between Region 3 discretionary spend per head and that of the region's own lower-middle income decile — a level people in the region already live at | Physical, from replacement cycles. Device life ~3–5 yrs, appliance life 8–12; doubling either halves the annual replacement flow | Dingel & Neiman 2020 and Sostero et al. 2020 both give 37% teleworkable for the US and EU; shaded to ~35% for the region's middle-income economies |
| **→ basket fraction** | 0.25 directly | 0.5 directly | 0.11 = commuting's ~30% share of household car distance × ~35% of workers |
| **Solved annual** | −389 Mt CO₂e/yr | −64 Mt CO₂e/yr | −155 Mt CO₂e/yr |
| **Cumulative, flat** | **−19.8 Gt** | **−3.3 Gt** | **−7.9 Gt** |
| **Copies** ⌊Gt⌋ | ⚠ 19 (sheet expects ~10) | 3 (sheet expects 3–5 ✓) | 7 (sheet expects ~9 ✓) |

**Cross-check worth keeping.** The contract estimated Basket A at "~1.4% per brick" from
literature; the table says **1.34%**. Two independent routes, same answer.

**Why remote work is ten times more carbon-intense per euro than buying less:** its basket
is nothing but fuel burnt at home, so almost every euro removed is combustion. Basket A is
mostly manufactured goods whose emissions sit in supply chains abroad.

### BUILD and SWAP — not yet solved

Records carry their fields so the export schema is right first time; `status = "pending"`.

| Tape | Ceiling | Basis |
|---|---|---|
| `eca_nuclear` | ⚠ 400 TWh/yr; §3 argues for ~650 reactors over a ten-year push — **19 kWh/d/p** | Industrial, not geological. Uranium and sites do not bind; concrete, forging and skilled labour do |
| `eca_geothermal` | 180 TWh/yr (~2 covers) — **0.55 kWh/d/p** | Geological and hotspot-gated: Iceland, Larderello, western Turkey, the Caucasus. A proven-hotspot floor with enhanced geothermal deliberately excluded — admitting EGS raises it an order of magnitude and it stops binding |
| `eca_fusion` | ⚠ carries 400 TWh/yr; **should carry none** | Not stock-gated. Its uncertainty is whether it works, which lives in the band |
| `eca_electric_vehicle_transition` | 320 M cars (~29 covers) — **0.36 cars/person** | The regional fleet less the share that cannot electrify this window — heavy rural use, and drivers without off-street parking where public charging is thin |
| `eca_ban_gas_supply` | 95 M homes (~8 covers) — **~1 home per 9.5 people** | Housing stock. ~105 M homes on mains gas; ~90% can take a heat pump without a fabric upgrade the tape does not pay for |
| `eca_smart_grid` | ⚠ carries 220 TWh/yr; **should be held** | Mechanism still under design. Assigning a number before that lands invents a ceiling for a tape whose shock is undecided |

---

## 5. Open reconciliations

1. **Weighted baskets.** The per-product lifetime cut rates need `apply_reduce` to take a
   factor per product rather than one for the basket. The `weight` column in the concordance
   exists for this and is currently 1.0 everywhere. It also decides the remote-work basket:
   with weights, the sheet's wider basket becomes *correct* rather than dilutive, because
   direct household emissions can track the fuel row alone instead of the basket average.
2. **Ceilings to realign:** buy-less down, nuclear up, fusion and smart grid to none.
3. **Columns cut by `eca_buy_less`:** households only, per the sheet.
4. **Region 3 workforce:** the sheet says ~300 M, the remote-work record assumed 400 M.

---

## 6. What every number here is still missing

**The 2011 → 2050 intensity correction.** These are 2011 intensities: a euro removed in 2011
carries more carbon than a euro removed in 2050 will, because the grid gets cleaner. One
scalar stands in for that today — see [`../../src/redworlds/engine/intensity.py`](../../src/redworlds/engine/intensity.py),
which is the single place it lives and the single place it will be replaced. It moves every
tape equally, so it cannot tilt one wing against another, which is what makes the
simplification safe to ship.

**Units.** All monetary figures above are 2011 basic-price million EUR, EXIOBASE's own.
See [`units_and_currency.md`](units_and_currency.md).
