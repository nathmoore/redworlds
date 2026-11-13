# How we predict the future

This page has two halves. The first explains, in plain terms, how Red Worlds predicts the
world's emissions if nobody intervenes: the scenario it follows, the world that gives in
2050, the factors that drive it, what the curve looks like so far, and how tonnes become
degrees. The second half, from [The picture](#the-picture) on, is the reference: every
input the walk reads and every assumption it makes, with the direction each one is likely
to push the answer.

The method and the plan for the steps not yet built are in
[`baseline_walk.md`](baseline_walk.md); the argument behind each simplification is in
[`assumptions.md`](assumptions.md).

**Keeping this current.** This page is updated in the same commit as any change to a step,
an input table or a default. A step that exists in code and not in the tables below is a
bug in this page.

**Status, 2026-11-13.** Three of thirteen steps are built and run as a hindcast from 2011
to 2025: economy size, spending mix and electricity. The walk does not yet run past 2025,
so there is no curve to 2050 or 2100 to show. Nothing here feeds a tape number yet, with
one exception: the income elasticities also weight the re-spend in SWAP tapes (see
[Rebound](#rebound-where-re-spent-money-goes)).

## How we predict the future

**We do not forecast. We write down a story and work out what it emits.** The model starts
from a detailed picture of the world economy in 2011. Each real-world trend that changes
emissions is written down as a number with a source, and applied one at a time. After each
one the economy is re-solved and the emissions are read off. We call this the *walk*. A
trend that is not written down does not happen: in that respect the world stays as it was
in 2011.

**The walk runs over the past first.** From 2011 to 2025 every trend is set to what was
observed, and the result is compared with measured emissions. Only a walk that can
reproduce the years we have records for is trusted with the years we do not.

**For the future, the story is "what we are doing now, carried forward".** The next section
says where that story comes from.

### The scenario: current policies, carried forward

The world's climate modelling centres agree a shared set of futures to simulate. The
current set, for the round called CMIP7, has seven
([Van Vuuren et al. 2026](https://doi.org/10.5194/gmd-19-2627-2026)), named for how their
emissions move: from *High*, through *Medium*, to *Very Low*. The walk follows **Medium**.

Medium answers one question: what happens if the world keeps doing what it is doing now? It
has two layers.

**People and the economy follow "middle of the road".** This is the second of five
storylines researchers share for how society might develop, the Shared Socioeconomic
Pathways ([O'Neill et al. 2017](https://doi.org/10.1016/j.gloenvcha.2015.01.004);
[Riahi et al. 2017](https://doi.org/10.1016/j.gloenvcha.2016.05.009)). In our words, SSP2
says:

> The world carries on much as it has. Social, economic and technological trends do not
> break sharply from their historical patterns. Incomes grow, unevenly: some countries
> make good progress and others fall short. Population growth is moderate and levels off
> in the second half of the century. Economies slowly use less energy and fewer resources
> per unit of output, and fossil fuel dependence eases without ending. Institutions work
> toward sustainability goals and make slow progress. Inequality improves only slowly.

Its numbers were updated in 2024 and 2025. World population peaks at about 10.1 billion
around 2080 and is about 9.9 billion in 2100
([KC et al. 2024](https://doi.org/10.5281/zenodo.7767425)), close to the United Nations' own
projection of a peak near 10.3 billion in the mid-2080s (*World Population Prospects
2024*).

**Climate policy stays where it was in 2025.** Only policies actually being implemented
count. Pledges and net-zero announcements that no law or budget yet backs are left out.
Those policies stay in place for the century and no new ones are added. Technology is still
allowed to improve on its own trend, so solar panels and batteries keep getting cheaper
(Van Vuuren et al. 2026, §3.3).

Three things make this the right world to measure an intervention against:

- **It contains no intervention.** Emissions level off and drift down, from about 40 Gt of
  CO₂ a year today to about 34 Gt in 2100. They never turn toward net zero. Any turn is
  something a tape does.
- **It gives credit for what has happened.** The older scenario sets included worlds with
  no climate policy at all and a very high emissions case. CMIP7 dropped both, because
  cheap renewables, existing policy and recent emission trends have made them implausible.
- **It is neither the best case nor the worst.** Its authors say it should not be read as
  the most likely future either. It is a benchmark: the consequences of the present
  course.

What Medium leads to, from a simple climate model run across the range of how the climate
might respond (Carbon Brief's
[explainer](https://www.carbonbrief.org/explainer-the-cmip7-emissions-scenarios-and-how-they-explore-future-climate-change),
2026, using the published scenario data):

| | Medium |
|---|---|
| CO₂ emitted, 2024 to 2100 | about 2,800 Gt |
| Warming passes 2 °C | around 2050 |
| Warming in 2100 | 2.9 °C, with a range of 2.2 to 3.9 |
| After 2100 | still rising; settles near 4 °C if emissions reach net zero during the 2100s (Van Vuuren et al. 2026, §4) |

**Medium is a description we follow, not a dataset we copy.** Each factor in the walk is
set on its own evidence, in the spirit of the two layers above. For clean technology that
means the International Energy Agency's Current Policies Scenario, which uses the same
rule as Medium: only what is already in law. The published Medium pathway is then what the
walk's result is compared with. See
[Reference scenarios](baseline_walk.md#reference-scenarios).

*Until November 2026 this page named the storyline as SSP2 alone and compared it with
SSP2-4.5, the nearest scenario in the previous set. Medium keeps SSP2's people and economy.
What changed is that the policy layer is now stated, and the comparison is with the
current scenario set.*

### The world of 2050

Tapes are played in the walk's 2050, so it helps to say what kind of world that is. None of
this is modelled as an event; it is what the assumptions add up to.

- **Larger and richer, unevenly.** More people than today and higher incomes, with most of
  the growth outside today's rich regions.
- **Cleaner for its size, and not clean.** Each unit of output carries less CO₂ than it
  does now. Total emissions are close to today's.
- **About 2 °C warmer than before industry.**
- **It has been trying.** The policies of 2025 were kept. Nothing was rolled back, and
  nothing on the scale of an emergency programme was attempted. People care about the
  environment and expect steady progress to be enough.

That last point is why 2050 is a point of decision. On its present course this world does
not reach net zero. The trade-offs it faces are the ones the tapes are built from:

- **Net zero or not, and how fast.** Medium has a sibling scenario, *Medium-to-Low*, which
  is the same world turning toward net zero from 2040. The walk's 2050 is the world that
  has not turned.
- **Long-lived things are being repriced.** Sea level keeps rising for centuries after
  temperature stops, so coastal land and buildings, and the insurance that covers them,
  depend on where warming ends up and not only on where it stands.
- **Thresholds lie ahead.** Medium's path beyond 2100 passes the central estimates for the
  dieback of part of the Amazon (about 3.5 °C) and for collapse of the Atlantic overturning
  circulation (about 4 °C), both with wide ranges
  ([Armstrong McKay et al. 2022](https://doi.org/10.1126/science.abn7950)).
- **Carbon removal is a promise, not yet a capacity.** Every lower scenario in the set that
  brings temperature back down relies on removing CO₂ from the air on a scale that has not
  been built (Van Vuuren et al. 2026, §4). Investing in it competes with everything else.
- **Building, swapping, or using less.** Scenario sets like this one mostly describe
  cleaner supply for the same services. Using less is the alternative they say least
  about, and it is one of the game's three kinds of tape (BUILD, SWAP, REDUCE).

The engine does not model sea level, tipping points or politics. It supplies tonnes. What a
game makes of them is the game's business.

### The factors

The walk's thirteen steps, grouped by what they do to emissions. Bold steps are built.

| What changes | Steps | Direction |
|---|---|---|
| **How much is bought** | **1 Economy size**: more people, higher incomes | Up, strongly. The engine of the whole curve |
| **What is bought** | **2 Spending mix**; 3 Food and diet | Small on the world total; shifts which products and regions |
| **How things are made** | 4 General productivity; 8 Industry energy; 12 Capital | Down. The largest brake in Cap et al. 2024's test of leaving each step out |
| **Where energy comes from** | **5 Electricity mix**; 6 Road transport; 7 Heating | Down. Clean power, then moving cars and heat onto it |
| **Smaller sources** | 9 Aviation and shipping; 10 Methane and nitrous oxide; 11 Data centres | Mixed |
| **Where things are made** | 13 Trade | Moves emissions between regions more than it changes the total |

The whole baseline is a contest between the first row and the rest: growth pushes
emissions up, and cleaner, leaner production pulls them down.

### What the curve looks like so far

The model reports fossil and industrial CO₂ here, which is what the observed record
measures best. Other gases (CO₂e) are carried in the table and join the comparison when
step 10 is built.

| Year | Growth only | All three built steps | Observed |
|---|---|---|---|
| 2011 | 32.5 Gt | 32.5 Gt | 34.5 Gt |
| 2015 | 37.6 | 37.4 | 35.5 |
| 2019 | 43.5 | 42.1 | 37.1 |
| 2025 | 52.0 | 48.5 | 39.0 |

What stands out:

- **If the world had only grown, emissions would be up 60% since 2011. They are up 13%.**
  The world economy grew 48% and population 16%. The gap between 60% and 13% is the work
  done by everything other than growth, and it is the thing the walk has to explain.
- **Growth happened in the carbon-heavy places.** Emissions under growth alone rise faster
  than the world economy (60% against 48%) because Mainland East Asia and South Asia more
  than doubled their economies, and the growth fell where each unit of output emitted more
  than the world average in 2011.
- **Each unit of world output now carries about a quarter less CO₂ than in 2011.** That
  is what "cleaner, leaner production" has amounted to in fourteen years.
- **Changing tastes barely move the total.** As people get richer they spend relatively
  less on food and more on travel and eating out. That is worth 0.07 Gt in 2025.
- **Cleaner electricity explains about a quarter of the gap** (3.4 Gt). Wind, solar and
  the retreat of coal in some regions are visible in the result.
- **The remaining 9.5 Gt is the unbuilt steps:** productivity, industry, and
  electrification of transport and heat.
- **Three regions hold most of the overshoot.** In 2025 the walk is 4.6 Gt high in
  Mainland East Asia, 3.0 Gt in Europe and Central Asia and 1.7 Gt in USA and Canada:
  about 85% of the regional total. These are the regions where the economy changed most
  in ways the walk does not yet describe. East Asia's economy more than doubled while its
  emissions rose 26%. Europe's and North America's economies grew while their emissions
  fell, by 16% and 8%.
- **Where little but growth happened, growth alone nearly fits.** Africa and Middle East
  lands on its observed figure, and South Asia is 14% high.
- **The model starts 6% low.** The 2011 table holds 32.5 Gt against 34.5 observed, so the
  two curves cross between 2011 and 2015.

What published work leads us to expect once the walk runs forward: under Medium, CO₂
emissions stay near today's level through the middle of the century and decline slowly,
to about 34 Gt a year in 2100, without approaching net zero (Van Vuuren et al. 2026;
Carbon Brief 2026). Our own curve is not drawn yet and may differ; when it is, it goes here
beside that one.

### From tonnes to temperature

The model returns tonnes of CO₂. Temperature comes from one line of arithmetic:

```
warming added  =  0.45 °C  ×  cumulative CO₂ emitted, in thousands of Gt
```

This works because of a well-tested regularity of the climate system: global warming is
close to proportional to the *total* CO₂ ever emitted, whenever and however fast it was
emitted. Two slow processes roughly cancel. The ocean keeps absorbing heat, which delays
warming, and land and ocean keep absorbing CO₂, which lowers its concentration. The ratio
is called the transient climate response to cumulative emissions (TCRE). Its best estimate
is 0.45 °C per 1000 Gt CO₂, with a likely range of 0.27 to 0.63
([IPCC 2021](https://www.ipcc.ch/report/ar6/wg1/);
[Allen et al. 2022](https://doi.org/10.1146/annurev-environ-112320-105050)).

Three things follow:

- **Temperature tracks the area under the emissions curve, not its height.** At today's
  39 Gt a year the world adds about 0.018 °C a year, or 0.18 °C a decade, from CO₂ alone.
  From 2011 to 2025 it emitted about 550 Gt: a quarter of a degree.
- **Warming stops, near enough, when net emissions reach zero.** It does not reverse. This
  is why the game scores cumulative tonnes abated: a tonne not emitted is a fixed sliver of
  warming avoided, wherever and whenever it happens.
- **An error in the baseline becomes an error in degrees.** The walk's present overshoot
  of 9.5 Gt a year, if it were carried unchanged to 2100, would overstate warming by about
  0.3 °C. This is the reason the hindcast gap must be closed before the walk is run forward.

**A check this line will face.** Medium emits about 2,800 Gt of CO₂ from 2024 to 2100. The
line turns that into about 1.3 °C of further warming, where the published figure for
Medium in 2100 implies rather more. Most of the difference is the other gases, described
next. When the walk reaches 2100, its temperature should be compared with Medium's on a
CO₂-only basis, or the other gases added.

What the line leaves out: it covers CO₂ only. Methane, nitrous oxide and the cooling effect
of air pollution add their own warming, which follows different rules (methane's depends on
the rate of emission more than the total). And 0.45 is a best estimate, so any temperature
carries the same ±40% as the ratio. The model itself stops at tonnes; the conversion is
done by whoever uses the result. For how the game uses it, see
[`red_carbon_contract.md`](red_carbon_contract.md).

## The picture

The model holds the world economy of 2011 as a table of who buys what from whom
(EXIOBASE 3.8.2, 200 products, aggregated to seven regions). Emissions come out of four
things multiplied together:

```
emissions  =  emission rates  ×  recipes  ×  what final consumers buy   +  fuel households burn
                   S               A → L              Y                          F_Y
```

- **What final consumers buy (`Y`)** is households, government and investment. Its total is
  GDP.
- **Recipes (`A`)** say what each industry buys to make one unit of output. Solving the
  table turns them into the full supply chain behind each purchase.
- **Emission rates (`S`)** say what each industry emits per unit of output.
- **Fuel households burn themselves (`F_Y`)**: petrol in cars, gas in boilers.

The walk changes those four things, one named real-world trend at a time, and re-solves.
Nothing is forecast by the model itself. A trend that is not written down as a step does
not happen: the world stays as it was in 2011 in that respect.

## What the walk believes throughout

These hold for every step, built or not.

| Belief | What it means | Where it pushes the answer |
|---|---|---|
| Constant 2011 prices | A euro buys the same physical amount in every year. Solar that became four times cheaper still costs its 2011 price | Understates how far cheap technologies spread on their own |
| No price response | Nobody buys more of something because it got cheaper, or less because it got dearer | Misses direct rebound, and substitution away from costly fuels |
| Linear recipes | Twice the output needs twice of every input. No economies of scale, no capacity limits | Small over the hindcast; grows with the horizon |
| Each buyer keeps its 2011 suppliers | A region whose demand grows pulls production from where it did in 2011 | Misses the shift of manufacturing between regions since 2011 |
| The size of each economy is set, not predicted | GDP is an input. A step that changes what is bought never changes how much is earned | By design; REDUCE tapes are the exception and state their GDP effect |
| One household per region | A region's households are one average buyer | Hides the spread between rich and poor, urban and rural |
| Annual totals | No hours, seasons, storage or dispatch | Cannot show how hard a wind-and-solar grid is to balance |
| Fossil and industrial CO₂ only in the check | Land-use emissions are outside the table | Diet and land steps will read lower than in the food literature |

Source for the method: the change-ratio approach of De Koning et al. 2016, Wiebe et al. 2018
and Cap et al. 2024.

## The steps that exist

Applied in this order. "Lands in" is the one part of the table the step is allowed to change.

### 1. Economy size

| | |
|---|---|
| **Says** | Each region's economy is as large as its real GDP says it was |
| **Lands in** | `Y`: every final-demand column of the region, by one factor |
| **Input** | Real GDP by region and year, 2011–2025: `data/baseline/economy.csv` |
| **Source** | World Bank World Development Indicators, NY.GDP.MKTP.KD (CC BY 4.0) |
| **Code** | `engine/economy.py`, `jobs/prepare_economy.py` |
| **Assumes** | Households, government and investment all grow at the GDP rate. Growth at market exchange rates. Taiwan follows the rest of Mainland East Asia |
| **Bias** | Run alone it overshoots, because nothing else has changed: 52 Gt for 2025 against 39 observed |

### 2. Spending mix

| | |
|---|---|
| **Says** | As income per head rises, households spend a smaller share on food and a larger share on travel, eating out and communication |
| **Lands in** | `Y`: the household column only, total unchanged |
| **Inputs** | Income elasticity by region and consumption category, and the product-to-category map: `data/baseline/income_elasticities.csv`, `data/concordances/exiobase_to_consumption_category.csv`. Income per head: real GDP over population, from `economy.csv` |
| **Source** | Bjelle et al. 2021, supplement (CC BY 4.0): elasticities estimated on EXIOBASE itself for its 49 regions and fifteen categories, 1995–2011. Formula: Cap et al. 2024, Eq. 1 |
| **Code** | `engine/spending.py`, `jobs/prepare_spending.py` |
| **Formula** | spending on a product × (1 + elasticity × change in income per head), then the basket is rescaled to its old total |

What it assumes, and which way each assumption leans:

- **Elasticities stay at their 2011 values.** In reality they drift as a region gets richer:
  food's falls further, and luxuries become ordinary. Over fourteen years this is minor.
  Over ninety it is not, and the step needs a saturation rule before it is used past 2050.
- **Fifteen categories, not 200 products.** Every product in a category moves together. One
  category, *Housing, real estate, water, gas, electricity and other fuels*, holds 97 of the
  200 products, including every fuel and every kind of electricity, with an elasticity
  close to one everywhere. So this step barely moves household energy use, which is where
  most household emissions are. Diesel is filed there too, as a heating fuel; petrol is
  under transport.
- **A game region's elasticity is an average of its members'**, weighted by what each
  spends on the category. Exact if members' incomes grow at the same rate.
- **Income per head is GDP per head.** The share of GDP that reaches households is held
  fixed.
- **Fuel burned by households follows their total spending**, which this step leaves alone,
  and not the share of it spent on fuel. Transport fuel has an elasticity of 1.2 to 1.6, so
  household direct emissions are slightly understated where incomes grew fast.
- **Government and investment keep their 2011 mix.**
- **Odd values are kept as published.** USA and Canada has 2.3 for fresh produce and 0.1
  for meat and dairy; the paper notes the United States as an outlier. They are not
  smoothed, because a smoothed figure would no longer be the cited one.

A check on the input: a household's budget shares times their elasticities must sum to one
(an extra euro is spent somewhere). The committed table gives 0.98 to 1.03 by region.

### 5. Electricity mix

| | |
|---|---|
| **Says** | Each region generates its electricity from the sources it was observed to use |
| **Lands in** | `A` and `Y`: which electricity products every buyer in the region takes its kWh from |
| **Input** | Observed generation by region, year and source: `data/baseline/electricity_generation.csv` |
| **Source** | Ember yearly electricity data (CC BY 4.0) |
| **Code** | `engine/electricity.py`, `jobs/prepare_electricity.py` |
| **Assumes** | Kilowatt-hours are conserved, not money. Each technology is as the 2011 table describes it. A technology the table describes badly in a region is replaced by a stand-in of the same class |
| **Bias** | Europe's result cannot be read yet: the table books much of its power sector under steam and hot water. Wind and solar carry 2011 supply chains, or a stand-in's |

Steps 3, 4 and 6 to 13 are designed in [`baseline_walk.md`](baseline_walk.md#the-steps)
and not built.

## Inputs at a glance

| File | What it holds | Derived from | Licence | Rebuilt by |
|---|---|---|---|---|
| `data/baseline/economy.csv` | Real GDP and population | World Bank WDI | CC BY 4.0 | `just prepare-economy` |
| `data/baseline/income_elasticities.csv` | Income elasticity and 2011 budget share, by region and category | Bjelle et al. 2021 supplement; EXIOBASE 3.8.2 for the shares | CC BY 4.0; CC BY-SA 4.0 | `just prepare-spending` |
| `data/concordances/exiobase_to_consumption_category.csv` | EXIOBASE product → consumption category | Bjelle et al. 2021 supplement | CC BY 4.0 | `just prepare-spending` |
| `data/baseline/electricity_generation.csv` | Observed TWh by source | Ember | CC BY 4.0 | `just prepare-electricity` |
| `data/baseline/electricity_observed.csv` | Observed power-sector totals, the check | Ember | CC BY 4.0 | `just prepare-electricity` |
| `data/concordances/ember_to_exiobase.csv`, `country_to_exiobase.csv` | Source and country maps | Written here | CC BY-SA 4.0 | by hand |
| Observed CO₂ (not committed) | The world and regional check | Global Carbon Budget via Our World in Data | to verify | downloaded |

## Rebound: where re-spent money goes

A SWAP that saves a household money leaves it with money to spend, and what it buys has a
footprint. A BUILD paid for by households leaves them with less. Both need an answer to one
question: **which spending moves when a household's budget moves?**

Two answers are built (`engine/balancing.py`, one argument):

- **Flat proportional.** A little more, or less, of everything, in proportion to the
  existing basket. This was the placeholder.
- **Income elasticity.** The money goes where an extra euro of income goes. A product's
  share of the re-spend is its budget share times its elasticity. The same table as step 2
  supplies the elasticities.

**Is that the right data for the job?** It is the best open source available, and it is not
a perfect fit. For:

- It is estimated on the same table the model runs on, for the same 49 regions, so no
  mapping between classifications is needed.
- Treating a saving as extra income is the standard first treatment of indirect rebound.
  Vita et al. 2019 and Wood et al. 2018 re-spend savings by existing expenditure patterns,
  which is the flat rule; elasticities are one step more faithful than that.
- It is CC BY 4.0, so the derived table can be committed.

Against:

- **It measures how spending follows national income over years, not what a household does
  with a windfall.** The two can differ: a saving on a fuel bill may be treated as fuel
  money and spent on more warmth or more driving.
- **That last effect, direct rebound, is not modelled at all.** A heat pump that makes
  warmth cheaper invites a warmer house. The same supplement publishes own-price
  elasticities by region and category, which is the data that effect would need.
- **Fifteen categories** cannot say whether freed money goes on flights or on train
  tickets; both sit in one category.
- **Elasticities describe households.** They say nothing about which investment is
  displaced when a BUILD crowds out other capital spending, so that case stays flat.

How it is wired today: SWAP tapes use elasticity weighting when the export job supplies the
table, and a record can keep the flat rule with `respend_weighting = "flat"`. BUILD remains
an injection by default (the game's rule). A BUILD record with `reallocate = true` and
`reallocate_from = "households"` is paid for out of household spending, weighted the same
way; no tape uses that yet.

## A physical cross-check

The table is in money, and money can drift from the physical world without anything
failing. MacKay's method in *Sustainable Energy — Without the Hot Air* is the check: state
each quantity per person per day and ask whether it is believable.

| Electricity generated, kWh per person per day | 2011 | 2025 |
|---|---|---|
| USA and Canada | 37 | 37 |
| Europe and Central Asia | 17 | 17 |
| Mainland East Asia | 11 | 22 |
| Latin America and the Caribbean | 7 | 8 |
| South East Asia and Pacific Ocean | 6 | 7 |
| Africa and Middle East | 3 | 4 |
| South Asia | 2 | 4 |
| World | 8.5 | 10.6 |

From the committed Ember and World Bank tables. MacKay puts Britain's electricity at
18 kWh per person per day, inside a total energy use of 125, and his plans for a Britain
that has electrified transport and heating need 48. So the steps still to come (electric
vehicles, heat pumps) should be judged against a rise of that order in rich regions, and a
walk that electrifies transport and heat without roughly doubling electricity per person
has lost energy somewhere.

## What the hindcast says so far

World CO₂ in Gt, each column adding one step. Observed is the Global Carbon Budget's fossil
and industrial series.

| Year | Economy size | + spending mix | + electricity mix | Observed | Over observed |
|---|---|---|---|---|---|
| 2011 (table as it stands) | 32.5 | 32.5 | 32.5 | 34.5 | −6% |
| 2015 | 37.63 | 37.62 | 37.4 | 35.5 | +5% |
| 2019 | 43.45 | 43.41 | 42.1 | 37.1 | +14% |
| 2025 | 51.95 | 51.88 | 48.5 | 39.0 | +24% |

Run 2026-11-12 with `just hindcast-walk`.

- **Growth alone overshoots by a third.** That is the size of what the other steps must
  explain.
- **The spending mix is worth 0.07 Gt in 2025**, a seventh of one per cent. Measured on
  households' own supply-chain footprint it is larger and uneven: −1.4% in South Asia,
  −0.5% in USA and Canada, −0.2% in Mainland East Asia and Europe, close to nothing
  elsewhere. Bjelle et al. 2021 found the same: a small effect on the world total, larger
  by region and product. The step matters for *what* is bought in 2050 more than for the
  total.
- **The electricity mix is worth 3.4 Gt**, a quarter of the gap.
- **9.5 Gt remains**, for the steps not built: productivity and efficiency, industry,
  electrification of transport and heat.

On the tapes, switching the re-spend from flat to income elasticity changes the two
consumer SWAP tapes on the 2011 table by −2.2% (electric vehicles: less abatement, because
freed money leans toward transport and eating out) and +0.2% (the household gas ban).

## Open, and what would close it

- **A saturation rule for elasticities** before step 2 is used past 2050: the
  reference-region method of Chen et al. 2022 (a region takes the elasticities of regions
  that have already reached its income), or the full demand system in Bjelle et al. 2021.
- **Household fuel following fuel spending**, as Cap et al. 2024 do, in place of following
  total spending.
- **Direct rebound**, from the own-price elasticities in the same supplement.
- **Whether a BUILD is ever paid for by households** is a game decision, not a modelling
  one.
- Everything under *Open for the designer* in
  [`../plans/03-baseline-walk.md`](../plans/03-baseline-walk.md).
