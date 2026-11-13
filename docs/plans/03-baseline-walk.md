# 03 — The baseline walk: 2011 → 2025 → 2050 → 2100

**Status: OPEN** (opened 2026-11-11).

The design this plan builds is in [`../design/baseline_walk.md`](../design/baseline_walk.md):
the method, the steps, the inputs and their sources. This file holds the build order, the
results so far and the decisions still to make.

**Designer intent (Nathan, confirmed 2026-11-11).** Walk the 2011 EXIOBASE table
forward ourselves, step by named step, so that the 2050 world the game is played in rests on
explicit, sourced assumptions about how the economy's structure changes: electricity,
electrification, sector composition, household spending, sector carbon efficiency. Check the
walk against what happened to 2025. From there the SSP2 "middle of the road" storyline guides
the assumptions we set, and published SSP2 projections are what we compare the result
against. Continue to 2100.

*Updated 2026-11-13 (Nathan):* the scenario is now named as CMIP7 *Medium*: SSP2 for people
and the economy, climate policy held at its 2025 level. The Medium pathway is the published
comparison. See *Decided*.

**Success criteria.**

1. A 2025 world built from the 2011 table reproduces observed emissions by major sector and in
   total, with the remaining gap reported per sector.
2. Every assumption is one row in a committed ledger: a value, a source, a licence, and the
   name of the matching IPCC scenario variable, so it can be set beside any published run.
3. A 2050 world replaces both constants in `engine/intensity.py` (issue #17) and is shown
   beside the published CMIP7 *Medium* pathway with the differences explained.
4. A sensitivity report sets the large uncertain levers side by side — AI data-centre
   electricity, how soon fusion works, how fast solar and wind get cheaper — and shows where
   each does and does not move regional and world CO₂.

**Added rigour (agent).** Hindcast before forecast, five-year snapshots, the source register
and its licence test, and the one-home-per-change rule. They serve the intent by making the
walk checkable; drop any that stop doing so.

---

## Resume here — handoff, 2026-11-12 (second session)

Three steps are built and run: economy size, spending mix, electricity. Read
[`../design/how_we_predict_the_future.md`](../design/how_we_predict_the_future.md) first: it lists what each
built step reads and assumes. The method is in [`../design/baseline_walk.md`](../design/baseline_walk.md).
The papers and reports are held outside this repo by Nathan; ask him for the folder.
Next, in this order:

1. **Technology cards from the IEA's *Energy Technology Perspectives 2026*** (CC BY 4.0). One
   CSV row per technology and scenario year: market status, deployment today, and
   deployment in CPS, STEPS and NZE for 2035 and 2050. Numbers in the report's text are
   exact; numbers on the dashboard charts have to be read off the images and should be
   marked approximate. Do not use the report's data annex or any IEA data file.
2. **Sprint item A5**, wind and solar recipes, which the cards and learning rates feed.
3. Then the sprint list below, from A4. **B3 and B4 are where the remaining 9.5 Gt is**:
   the spending step turned out to be worth 0.07 Gt, so nothing more on household baskets
   will close the hindcast gap.

Not yet done: the *World Energy Outlook 2025* is unread; the fusion figures are from
summaries and unconfirmed; the tape table has not been re-exported since the re-spend rule
changed.

## Sprint plan

The build order, newest state first. Each numbered item is sized for one working session.
Tick items here as they land; findings go under *Milestone A results* below.

**Done**

- [x] **A1 Data preparation for electricity** (2026-11-11). `just prepare-electricity` turns
  Ember's country data into `data/baseline/electricity_generation.csv` (targets) and
  `electricity_observed.csv` (the check), through two committed concordances.
- [x] **A2 The electricity step** (2026-11-11). `engine/electricity.py`, conserving kWh, with
  a reliability test per technology and a stand-in rule. Tested on the pymrio test world.
- [x] **A3 First electricity-only hindcast** (2026-11-11). `just hindcast-electricity`.
- [x] **Reliability check across all products** (2026-11-12). `just diagnose-intensities`
  writes `data/baseline/intensity_outliers.csv`; findings in
  [design § Which regions can describe which products](../design/baseline_walk.md#which-regions-can-describe-which-products).
- [x] **B1 Economy size** (2026-11-11). `engine/economy.py` scales each region's final demand
  by its real GDP growth; `just prepare-economy` builds `data/baseline/economy.csv` from
  World Bank data; `just hindcast-walk` runs both built steps against observed CO₂.

- [x] **B2 Spending mix** (2026-11-12). `just prepare-spending` turns the supplement to
  [Bjelle et al. 2021](https://doi.org/10.1016/j.eneco.2021.105114) into `data/baseline/income_elasticities.csv` and a product
  concordance; `engine/spending.py` applies them as in [Cap et al. 2024](https://doi.org/10.1016/j.spc.2023.12.031) Eq. 1. The
  supplement held the elasticities themselves for all 49 regions, so they are used
  directly and the six region groups and projected shares were not needed.
- [x] **Elasticity-weighted re-spend for SWAP** (2026-11-12). `rebalance_economy` takes
  weights; the tape export passes the same elasticities. Backlog: "Rebalancing weighting
  scheme".

**Next, in order**

1. **A4 Locate Region 3's heat-and-power plants.** The first run found that the table books
   much of Europe's power sector under *Steam and hot water supply services* (backlog:
   "Region 3's power sector is split between two products"). Confirm by country on the
   49-region table, then decide whether that product is walked with electricity or under
   heating. Needs the full table parsed: about twenty minutes and 3 GB.
2. **A5 Give wind and solar recipes from outside the table.** They fail the reliability test
   in several regions, so a fifth of East Asia's 2025 generation runs on a stand-in.
   Borrowing between regions does not fix it: solar PV passes the test only in USA and
   Canada, where the table gives it 194 g of direct CO₂ per kWh, and the table's wind
   carries 5 to 300 g. The precedent is [Wiebe et al. 2018](https://doi.org/10.1186/s40008-018-0118-y), who build each technology's
   capital input from a cost breakdown (their SI Table SI1, already the source of this
   repo's BUILD capex split):

   | | Machinery (29) | Electrical machinery (31) | Construction (45) | Insurance (66) | Other business (74) | Life |
   |---|---|---|---|---|---|---|
   | Solar PV | | 76% | 12% | | 11% | 25 y |
   | Wind, onshore | 69% | 7% | 13% | 3% | 7% | 25 y |

   A recipe per kWh then needs four more numbers per technology, each a ledger row with a
   source: installed cost per kW, capacity factor, operating cost, and zero direct
   emissions. IRENA's *Renewable Power Generation Costs in 2024* gives installed costs of
   about USD 691 per kW for solar PV and USD 1,041 for onshore wind (from summaries of the
   report; confirm in the report itself, with its capacity factors and reuse terms).
   The recipe is read from a maturity curve by build year
   ([design § Technology maturity](../design/baseline_walk.md#technology-maturity)), so this item starts with data
   preparation: installed cost and capacity added by year, for solar PV and onshore wind.
   Forward costs follow [Way et al. 2022](https://doi.org/10.1016/j.joule.2022.08.009)'s learning rates (20% per doubling for solar,
   13% for wind), which need only the capacity path as input.
3. **A6 The walk's skeleton.** A general ledger loader with the `status` column, a
   `jobs/walk_baseline.py` that applies steps in order and caches each snapshot, and the
   version stamp. The electricity hindcast becomes its first caller.
4. **B3 Road transport and heating.** Data preparation for EV stock and heat pumps; apply
   `apply_swap`'s mechanism at baseline scale.
5. **B4 Industry, productivity and non-CO₂**, then the residual by sector against observed
   emissions. Closes Milestone B.
6. **B5 Trade and where things are made.** Measure first: compare each region's import
   shares by product group in the 2011 table with EXIOBASE 3.8.2's 2019 table, and the
   regional split of output with observed value added by sector. If sourcing moved enough
   to matter, add step 13.
7. **C1 Forward population and GDP.** `just prepare-economy` gains the years after 2025.
   Population from the 2025-rebased SSP2 projections of KC (Zenodo, CC BY 4.0: countries,
   five-year steps to 2100; filter on its region-level column before summing). GDP needs a
   decision first: see *Open for the designer* 6.
8. **C2 The Medium comparison.** A small hand-entered table of Medium's headline figures
   with their sources (CO₂ per year at 2030, 2050 and 2100, the cumulative total,
   population, warming), and a report that sets the walk beside it. See
   [design § Tracking against CMIP7 Medium](../design/baseline_walk.md#tracking-against-cmip7-medium).
   Before entering anything, read the explorer's variable and region definitions.
9. **C and D** as under *Milestones*.

A run of the hindcast takes ten to thirty minutes on an 8 GB laptop at seven regions. Item 1
is the only one that needs the full 49-region table.

## Milestone A results

First run, 2026-11-11: every region's electricity mix walked from the 2011 table to the
observed mix of each year, everything else held at 2011.

| Region | Model 2011 | Model 2025 | Change | Observed 2011 | Observed 2025 | Change | Stand-in 2025 |
|---|---|---|---|---|---|---|---|
| Europe and Central Asia | 369 | 262 | −29% | 405 | 284 | −30% | 9% |
| USA and Canada | 465 | 318 | −32% | 504 | 360 | −29% | 0% |
| Mainland East Asia | 723 | 532 | −26% | 725 | 525 | −28% | 22% |
| South East Asia and Pacific | 529 | 499 | −6% | 572 | 542 | −5% | 11% |
| South Asia | 798 | 772 | −3% | 722 | 671 | −7% | 11% |
| Latin America and Caribbean | 266 | 215 | −19% | 292 | 249 | −15% | 13% |
| Africa and Middle East | 626 | 535 | −15% | 648 | 592 | −9% | 4% |

Grams per kWh. Model: direct CO₂ from the table. Observed: Ember's lifecycle CO₂e.

What it shows:

- **The step works.** The modelled fall in carbon intensity follows the observed fall in the
  four largest regions to within three percentage points.
- **The level sits about 8% under Ember's** in most regions, which is the expected gap
  between direct CO₂ and lifecycle CO₂e. South Asia is the exception, 10–15% above: the
  table's coal there emits 1,067 g per kWh.
- **The 2011 table does not hold Ember's 2011 mix.** Left as it stands, the table's Europe
  generates at 274 g per kWh, not 369, and supplies 3,337 TWh against 5,074 observed. The
  rest is under *Steam and hot water supply services* (item A4). World-wide the table's
  electricity products supply 18,940 TWh against 22,036 observed.
- **Mix change alone is worth about 7% of world CO₂.** With 2011 demand, world CO₂ falls from
  32.9 Gt on the 2011 mix to 30.5 Gt on the 2025 mix.
- **Stand-ins are not a detail.** They cover a fifth of East Asia's generation by 2025 (A5).

## Results with three steps: economy size, spending mix, electricity

Run 2026-11-12. World CO₂ in Gt, each column adding one step; observed is the Global Carbon
Budget's fossil and industrial series.

| Year | Economy size | + spending mix | + electricity mix | Observed | Over observed |
|---|---|---|---|---|---|
| 2011 (table as it stands) | 32.5 | 32.5 | 32.5 | 34.5 | −6% |
| 2015 | 37.63 | 37.62 | 37.4 | 35.5 | +5% |
| 2019 | 43.45 | 43.41 | 42.1 | 37.1 | +14% |
| 2025 | 51.95 | 51.88 | 48.5 | 39.0 | +24% |

What it shows:

- **The starting point is close.** The 2011 table is 6% under observed world CO₂, and each
  region is within 7%.
- **"The 2011 world, bigger" overshoots by a third.** Growth alone gives 52 Gt for 2025.
- **The spending mix barely moves the total**: 0.07 Gt in 2025. On households' own
  supply-chain footprint it is −1.4% in South Asia, −0.5% in USA and Canada, −0.2% in
  Mainland East Asia and Europe. This agrees with [Bjelle et al. 2021](https://doi.org/10.1016/j.eneco.2021.105114), and has a plain
  cause: every fuel and all electricity sit in one consumption category whose income
  elasticity is close to one.
- **The electricity mix closes about a quarter of the gap** (3.4 of 13 Gt).
- **The remaining 9.5 Gt is what the unbuilt steps must explain**: efficiency and
  productivity, industry, electrification of transport and heat. That is the same ordering
  [Cap et al. 2024](https://doi.org/10.1016/j.spc.2023.12.031) found, where productivity was the largest brake.
- **By region for 2025:** Africa and Middle East lands on observed; South Asia and South
  East Asia are 14–15% over; Latin America 20%, USA and Canada 30%, Mainland East Asia 35%,
  Europe and Central Asia 57%.
- **Europe moves the wrong way under the electricity step** (8.34 Gt before it, 8.35 after,
  and higher with it in 2015 and 2019). Imposing the observed mix raises its emissions
  because the table books its heat-and-power plants outside electricity (sprint item A4).
  Until that is resolved, Europe's electricity result should not be read.

Regional observed figures are territorial and exclude international aviation and shipping;
the model's regional figures include what each region's carriers emit.

## Decided

- **The baseline scenario is CMIP7 *Medium*** (Nathan, 2026-11-13). Until now the walk named
  SSP2 as its storyline and compared itself with SSP2-4.5 and other SSP2 runs. The CMIP7
  scenario set (Van Vuuren et al. 2026) replaced that framework in 2026. Its *Medium* is
  what this plan was already building: SSP2's population and economy, and only the climate
  policy already in force, which is the Current Policies rule decided on 2026-11-12. So the
  walk's assumptions do not change. What changes is the name, the comparison curve, and
  the population and GDP sources, which move to the 2024/25 SSP update. The rationale is in
  [design § The scenario](../design/how_we_predict_the_future.md#the-scenario-current-policies-carried-forward)
  and [`assumptions.md`](../design/assumptions.md). References to "the SSP2 walk" in the
  current docs and code were renamed the same day; closed plans 01 and 02 and ticked
  backlog items keep the old wording as history.
- **Technologies are described by maturity curves, not one vintage** (Nathan, 2026-11-11).
  Cost and performance by build year, with a learning curve forward and a range for
  technologies with no track record. See
  [design § Technology maturity](../design/baseline_walk.md#technology-maturity). This settles the vintage
  question raised under sprint item A5: the fleet in each snapshot is a mix of build years.
- **The baseline reaches 2100, so unproven technologies get a central path** (Nathan,
  2026-11-12): an invented recipe, a first year and a deployment path with a range, all
  marked as assumptions. See [design § Technology maturity](../design/baseline_walk.md#technology-maturity).
- **IEA and MacKay are read side by side** (Nathan, 2026-11-12). The IEA's outlook is that of
  building and swapping; MacKay's physical arithmetic is the check that keeps it from
  becoming the frame. See [design § Reference scenarios](../design/baseline_walk.md#reference-scenarios).
- **Baseline technology growth follows the IEA's Current Policies Scenario unless a ledger
  row states an exception and its reason** (Nathan, 2026-11-12). *Energy Technology
  Perspectives 2026* also sets which technologies the walk treats explicitly.
- **Bjelle et al. 2021's data is used for spending shares and for rebound** (Nathan,
  2026-11-12): the paper and its supplement are CC BY 4.0, so derived tables are committed
  with attribution. Built the same day; the case for and against using it for rebound is in
  [design § Rebound](../design/how_we_predict_the_future.md#rebound-where-re-spent-money-goes).
- **The IEA's scenarios are the reference set** (Nathan, 2026-11-12). Baseline levers are read
  against Current Policies and Stated Policies; tapes are measured against Net Zero
  Emissions by 2050. Technologies are described in the style of the IEA's technology
  dashboards. SSP2 stays the storyline for the walk's own assumptions. See
  [design § Reference scenarios](../design/baseline_walk.md#reference-scenarios).
- **Physical-to-money conversion is a designed, stated input** (Nathan, 2026-11-11), shared
  by the walk and the tapes and free to differ by tape and year. See
  [design § Prices are an input](../design/baseline_walk.md#prices-are-an-input).
- **SSP2 is the storyline, not a dataset** (Nathan, 2026-11-11). Each lever is set on
  evidence in the spirit of SSP2: trends do not shift markedly from historical patterns
  ([O'Neill et al. 2017](https://doi.org/10.1016/j.gloenvcha.2015.01.004); [Riahi et al. 2017](https://doi.org/10.1016/j.gloenvcha.2016.05.009) — quote the paragraph when this plan opens).
  Published SSP2 series are the comparison. No milestone waits on a scenario dataset.

## Open for the designer

1. Electricity built from demand and supply with fossil filling the gap
   ([design § Electricity](../design/baseline_walk.md#electricity)).
2. Data centres: IEA base case in the baseline; its high case, and a run-on to 2050, as
   sensitivities.
3. Walk the seven game regions (minutes per snapshot), with electricity computed from country
   data before aggregating; the alternative is all 49 EXIOBASE regions.
   *Proposed 2026-11-13 (Nathan), not decided:* make the resolution a switch. Seven regions
   for building and testing; all 49 for the walks that are published; the 2050 world
   aggregated to seven for the game. What this needs: input ledgers kept at EXIOBASE-region
   level and aggregated on load, steps that take whatever region list the table has, and
   first a one-off comparison of the economy-size step at 7 and at 49 to see how much the
   answer moves. All 200 products are already kept, so only regions are in question.
4. The pass mark proposed under [Checking the walk](../design/baseline_walk.md#checking-the-walk).
5. Whether the game wants the urban and rural households.
6. **An open source for GDP after 2025.** The SSP2 GDP projections (OECD, in the SSP basic
   elements v3.2) are under a licence that forbids reproducing a substantial portion, so
   they cannot be a committed input. Options: (a) cite regional growth rates from the
   published papers and enter them by hand as ledger rows, a few numbers per region;
   (b) build GDP from the open population projections and a stated income-per-head path
   per region, checked against the published totals; (c) ask IIASA for permission.
   (a) is the least work and stays within the licence if the rows are few.

## Milestones

A can start now; each later one builds on the one before.

- **A. Electricity-only hindcast** — first run done; see *Sprint plan* and *Milestone A results*.
- **B. Full hindcast to 2025.** Steps 1–10 and 12 on observed values; residual by sector.
- **C. To 2050.** Levers set under CMIP7 *Medium*; step 11 and its sensitivity. Replaces
  the constants in `engine/intensity.py` and re-bases every tape.
- **D. 2050 to 2100.** Open question: tapes re-solved at later snapshots, or scaled along the
  baseline's intensity path.

## To verify

- The Global Carbon Budget's own data terms. Its fossil CO₂ series (38.6 Gt for 2024, 39.0 Gt
  projected for 2025, as distributed by Our World in Data) is used as a check and not
  committed until they are confirmed.
- Which countries EXIOBASE puts in each rest-of-world block. `country_to_exiobase.csv` assigns
  them by continent, which is an assumption.
- Every licence marked **?**. Two were tried on 2026-11-13 and not found: the UN's terms for
  *World Population Prospects 2024*, and the Global Carbon Budget's (neither site's pages
  stated them where looked).
- ~~The release name and licence of the IIASA SSP basic-drivers update.~~ Checked
  2026-11-13: "SSP basic elements v3.2", May 2025, GDP and population only (urbanisation
  not yet updated). IIASA's adapted licence: citable, not a ledger input. Recorded in
  [design § Sources](../design/baseline_walk.md#sources).
- Whether the ScenarioMIP explorer's variable list includes electricity by source and
  final energy for Medium, and which regions it uses.
- The 2100 temperature the walk should be compared with on a CO₂-only basis.
