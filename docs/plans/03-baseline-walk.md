# 03 — The baseline walk: 2011 → 2025 → 2050 → 2100

**Status: DRAFT 2026-11-11 — work started on Milestone A at Nathan's direction; the intent
and success criteria were drafted by an assistant and still await his confirmation.** Design
choices below are the plan's working design; the ones that need his call are listed once,
under *Open for the designer*.

**Designer intent (Nathan — drafted, to confirm or rewrite).** Walk the 2011 EXIOBASE table
forward ourselves, step by named step, so that the 2050 world the game is played in rests on
explicit, sourced assumptions about how the economy's structure changes: electricity,
electrification, sector composition, household spending, sector carbon efficiency. Check the
walk against what happened to 2025. From there the SSP2 "middle of the road" storyline guides
the assumptions we set, and published SSP2 projections are what we compare the result
against. Continue to 2100.

**Success criteria (drafted).**

1. A 2025 world built from the 2011 table reproduces observed emissions by major sector and in
   total, with the remaining gap reported per sector.
2. Every assumption is one row in a committed ledger: a value, a source, a licence, and the
   name of the matching IPCC scenario variable, so it can be set beside any published run.
3. A 2050 world replaces both constants in `engine/intensity.py` (issue #17) and is shown
   beside published SSP2 runs with the differences explained.
4. A named sensitivity for AI data-centre electricity shows where it does and does not move
   regional and world CO₂.

**Added rigour (agent).** Hindcast before forecast, five-year snapshots, the source register
and its licence test, and the one-home-per-change rule. They serve the intent by making the
walk checkable; drop any that stop doing so.

---

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

**Next, in order**

1. **A4 Locate Region 3's heat-and-power plants.** The first run found that the table books
   much of Europe's power sector under *Steam and hot water supply services* (backlog:
   "Region 3's power sector is split between two products"). Confirm by country on the
   49-region table, then decide whether that product is walked with electricity or under
   heating. Needs the full table parsed: about twenty minutes and 3 GB.
2. **A5 Re-base the technologies the table cannot describe.** Wind and solar fail the
   reliability test in several regions, so a fifth of East Asia's 2025 generation runs on a
   stand-in. Two different fixes are needed:
   - *Wind* is reliable in most regions, so a region that lacks it can borrow the recipe and
     emission rate of the regions that have it (generation-weighted), with purchases
     rescaled to the borrowed price so kWh are conserved.
   - *Solar PV* passes the test only in USA and Canada, and there the table gives it 194 g
     of direct CO₂ per kWh, so there is nothing sound to borrow. It needs a recipe from
     outside the table: a capital-cost split by product (the kind [Wiebe et al. 2018](https://doi.org/10.1186/s40008-018-0118-y) SI
     Table SI1 gives, already used for BUILD capex), a capital cost per kW, a lifetime and a
     capacity factor, and zero direct emissions. Each of those is a ledger row needing a
     source, so this half is a modelling decision before it is code.
3. **A6 The walk's skeleton.** A general ledger loader with the `status` column, a
   `jobs/walk_baseline.py` that applies steps in order and caches each snapshot, and the
   version stamp. The electricity hindcast becomes its first caller.
4. **B1 Economy size.** Data preparation for population and GDP by game region, 2011–2025
   (check the UN and World Bank licences first), then step 1 through the existing
   `scale_final_demand`. First hindcast with demand growing.
5. **B2 Spending mix.** Needs the elasticities from [Bjelle et al. 2021](https://doi.org/10.1016/j.eneco.2021.105114) (paper and data
   still to obtain). Until then a flat placeholder, marked as one in the ledger.
6. **B3 Road transport and heating.** Data preparation for EV stock and heat pumps; apply
   `apply_swap`'s mechanism at baseline scale.
7. **B4 Industry, productivity and non-CO₂**, then the residual by sector against observed
   emissions. Closes Milestone B.
8. **C and D** as under *Milestones*.

A run of the hindcast takes about nine minutes on an 8 GB laptop at seven regions. Item 1
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

## The method

EXIOBASE computes emissions from three tables, so a walk can change three things:

- **Final demand (`Y`)** — how much is bought, and of what.
- **Recipes (`A`)** — what each industry buys to make one unit of output.
- **Emission rates (`S`, and `F_Y` for fuel that households burn directly).**

Each real-world trend is assigned to one of those, the steps are applied in a fixed order,
and the system is re-solved. Emissions are a result; the world total is a check.

1. **One home per change.** A fuel saving goes into the recipe or the emission rate, not both.
2. **Constant 2011 prices.** A physical change (TWh, vehicle-km) becomes money at the table's
   own implied price: its euros for that product divided by the observed 2011 quantity.
3. **Five-year snapshots**, each built on the one before: 2015 to 2050, then decadal to 2100.
4. **Each step keeps column totals**, and the accounting identity is asserted after it.

This is the change-ratio method of [De Koning et al. 2016](https://doi.org/10.1080/14693062.2014.999224), [Wiebe et al. 2018](https://doi.org/10.1186/s40008-018-0118-y) and [Cap et al. 2024](https://doi.org/10.1016/j.spc.2023.12.031), applied to the product-by-product table through `pymrio`.

## The steps

"Driven by" is the evidence a ledger row cites for the step's size. Long-term integrated
models derive these from prices and costs; this walk has no prices, so it uses observed
trends, adoption S-curves, and the reference-region method of [Chen et al. 2022](https://doi.org/10.1038/s41597-022-01209-5) (take the
speed from regions that have already passed this level, re-check every five years).

| # | Step | Lands in | Driven by | Code |
|---|---|---|---|---|
| 1 | Economy size | `Y` | Population × income per head, per region. This *sets* GDP: in an input-output table GDP equals final demand | `scale_final_demand` |
| 2 | Spending mix | `Y` | Income elasticity per product, with saturation; age structure, household size and urban share (see Households) | per-product scaling, extend |
| 3 | Food and diet | `Y`, `S` | Diet by income (meat and dairy rise, then level off; food elasticities fall as income grows, [Zhao et al. 2022](https://doi.org/10.3390/nu14224711)) from reference regions; food-waste share; farm emission rates. Comparison: [Springmann et al. 2018](https://doi.org/10.1038/s41586-018-0594-0)'s middle-of-the-road baseline, food-system pressures up 50–90% from 2010 to 2050 without mitigation | new |
| 4 | General productivity | `A` | Observed fall in inputs needed per unit of output. The largest brake on emissions in Cap et al.'s leave-one-out test. Excludes the energy savings counted in step 8 | new |
| 5 | Clean electricity supply | `A`, `Y` | Generation built by source and region; coal and gas retirement by stated plant life (see Electricity) | BUILD operating phase, generalise |
| 6 | Road transport | `Y`, `F_Y`, `A` | EV share of the fleet on an S-curve fitted to sales, capped by fleet turnover; electricity at about a third of the fuel energy | `apply_swap`, road `F_Y` share |
| 7 | Heating | `Y`, `F_Y`, `A` | Heat-pump share of heating, capped by boiler turnover; COP about 3 | `apply_swap` |
| 8 | Industry energy | `A` | Observed efficiency trend by sector; fuel switching; steel and cement demand per head saturating | new |
| 9 | Aviation and shipping | `A`, `S` | Sector trends | new, small |
| 10 | Methane and nitrous oxide | `S` | Reduction ratios for agriculture, waste and energy | new, small |
| 11 | Data centres | `A` | TWh, as electricity bought by *Computer and related services (72)* and *Post and telecommunication services (64)* | new, small |
| 12 | Capital | `A` | Capital needed per unit of output, by technology (see Capital) | extend `engine/capital.py` |

Sector shift toward services is not a step: it falls out of steps 1–4 and is checked against
observed value-added shares.

Urbanisation is not a step either. Its effect on a region's total footprint is small (3–7% in
the EU, [Ottelin et al. 2019](https://doi.org/10.1088/1748-9326/ab443d), cited in [Cap et al. 2024](https://doi.org/10.1016/j.spc.2023.12.031)), and it acts through steps 2, 6 and 7.
It enters as a demographic input to step 2.

## Electricity

Electricity has no "mix" input. It is built from demand and supply:

- **Demand** is a result. Steps 6, 7, 8 and 11 each raise somebody's electricity purchases,
  and the solve adds them up.
- **Clean supply** is an input: generation by source and region (solar, wind, nuclear, hydro),
  from capacity added and typical output.
- **Fossil generation fills the gap** between the two, within what has not been retired. Each
  region's ledger states which fossil source fills it.

Under this rule extra demand from data centres or EVs is met by whatever is left over, so the
walk can show whether it slows the fossil exit or is absorbed by clean build-out. That is
what the data-centre sensitivity needs; a fixed-share mix would serve new demand at the
average and could not show it.

It is an annual energy balance. The table has no hours, dispatch or storage, the same limit
the Smart Grid tape states.

## Households

Step 2 derives each region's household basket from demographic rows in the ledger: age
structure, household size, urban share and income distribution. Heating and appliances
follow the number of households; ageing moves spending toward health and home energy and
away from commuting. The model keeps one household column per region.

**Optional extension: an urban and a rural household.** Split a region's household column by
its urban population share, with a small table of multipliers per spending group (rural: more
vehicle fuel and heating, fewer services), scaled so the two columns add back to the
original. Because they add back, a rough multiplier changes who holds the footprint and not
the region's total, so it can start as a placeholder and be refined with survey data
(Eurostat Household Budget Survey by degree of urbanisation and income, for Europe). Its
purpose is to let a tape act on one group. Build it for Region 3 when the game wants that.

## Capital

Capital is endogenised in the 2011 baseline ([Södersten et al. 2018](https://doi.org/10.1021/acs.est.8b02791)), so when demand grows or
shifts, the construction and machinery behind it follow, separately for each electricity
source. Three things the walk has to do:

1. **Store the capital coefficients separately.** The cached world merges them into `A`; the
   walk needs to change them on their own.
2. **Re-base wind and solar.** The 2011 table does not describe them consistently. Its
   money output per TWh of solar PV runs from under 1 million EUR in Latin America to 194
   million in Africa and Middle East, against mostly 30 to 250 for coal, gas, nuclear and hydro
   (Milestone A technology table). Since every input, capital included, is recorded per
   euro of output, the inputs behind a kWh of solar vary by the same factor, and in most
   regions are far too small. Sprint item A5 replaces such a technology's recipe with a
   borrowed one. Updating that recipe from 2011 costs to current ones is then a separate
   lever, and is where assumptions about 2050 construction costs and efficiencies enter.
3. **Decide on the 2011 construction trough** at the first snapshot (see the backlog
   diagnostic under *BUILD capex (a)*).

## How the code is organised

The walk follows the tapes' pattern, so an assumption can begin as a placeholder and be
replaced between game campaigns.

- **One step, one pure function** in `engine/`, with its own test on `pymrio.load_test()`.
- **One ledger**, a committed CSV: step, region, year, value, source, licence, IPCC variable
  name, and a status of `placeholder`, `provisional` or `ready`.
- **One job** applies the steps in order and caches each snapshot, so re-running from 2030
  does not rebuild 2015.
- **A version stamp** on the baseline, carried in the tape export.

Changing an assumption is: edit a ledger row, rebuild the baseline, re-export the tapes. A
placeholder is acceptable where a wrong value costs accuracy but cannot tilt one wing or tape
against another, the test `engine/intensity.py` states.

## Checking the walk

- **Checkpoints.** 2015 (last observed energy data in EXIOBASE 3.8.2), 2019 (last observed
  GHG data) and 2025. Compare emissions, physical quantities and shares, not euros: the walk
  is in 2011 prices and later EXIOBASE tables are in current prices. 2020 is computed but not
  used as a checkpoint; landing on observed 2025 carries whatever persisted from the pandemic,
  including today's level of remote work, which the remote-work tape's ceiling must net out.
- **Residual by sector.** A change in emissions between two years splits exactly into
  population, spending per head, spending mix, recipes and emission rates (structural
  decomposition). The steps name drivers for all five; the residual is what the named drivers
  miss.
- **Leave one out**, as Cap et al. do, to see which steps carry the result.
- **Beside SSP2.** Plot each lever and the totals against published SSP2 runs.

Proposed pass mark: in each major sector the residual is smaller than the effect of the tapes
that act on that sector.

## After 2050, and outside the table

Some things the table cannot represent: land-use emissions (the CO₂ row excludes them),
carbon removal, and products with no 2011 row such as hydrogen. These are taken from
published SSP2 runs and labelled as borrowed, which is accepted practice for a model with
narrower boundaries ([Krey 2014](https://doi.org/10.1002/wene.98)). One visible consequence: diet tapes will read lower here
than in the food-systems literature, where land carries much of the benefit.

The input-output walks this plan follows stop at 2050. For 2050–2100 the walk carries fewer
levers with wider ranges. Trade structure, who makes what for whom, stays as the steps leave
it unless a trade scenario is added by the Beaufils & Wenz method. Across long-term models the carbon intensity of energy supply
becomes the dominant lever by 2100, as long-lived plant turns over ([Krey 2014](https://doi.org/10.1002/wene.98)), so the supply
rows matter most there. Where a lever depends on a current policy, its ledger row says
whether the policy is assumed to continue, strengthen or lapse.

## Sources

Full citations, each checked against its DOI record, are in
[`../references.md`](../references.md#the-baseline-walk-plan-03).

**The licence test.** This repo is public and CC BY-SA 4.0. A source's data may be committed
in the ledger only if it allows redistribution and share-alike (public domain, CC0, CC BY,
CC BY-SA). Any other source can be cited for a figure but cannot be a ledger input.

Licence column: **✔** checked on the publisher's page 2026-11-11; **?** not yet checked;
**✘** checked and fails.

### Proposed

| Step | Observed 2011–2025 | Evidence for 2026–2100 | Licence |
|---|---|---|---|
| 1 | UN World Population Prospects; World Bank WDI | IIASA SSP basic drivers (2024/25 update), SSP2 | ? ; ? ; ? |
| 2 | Household expenditure by purpose (Eurostat, OECD); Wittgenstein Centre population by age; [Chen et al. 2022](https://doi.org/10.1038/s41597-022-01209-5) urban share | [Bjelle et al. 2021](https://doi.org/10.1016/j.eneco.2021.105114) elasticities; [Rao et al. 2019](https://doi.org/10.1016/j.futures.2018.07.001) income distribution | ? |
| 3 | FAO food balances; [Poore & Nemecek 2018](https://doi.org/10.1126/science.aaq0216) for the food chain total (about 13.7 Gt CO₂e, 26% of emissions) as a check | Reference regions; [Springmann et al. 2018](https://doi.org/10.1038/s41586-018-0594-0) baseline | ? |
| 4, 8 | EDGAR sector emissions; [PRIMAP-hist **v2.6**](https://zenodo.org/records/13752654) | AR6 scenario database, SSP2 runs | ? ; ✔ CC BY 4.0 ; ? |
| 5 | [Ember yearly electricity data](https://ember-energy.org/data/electricity-data-explorer/) by country and source | IRENA capacity statistics; IEA World Energy Outlook (cite) | ✔ CC BY 4.0 ; ? |
| 6 | IEA Global EV Outlook; fleet statistics | same, by scenario | ? |
| 7 | Eurostat energy balances; heat-pump sales | — | ? |
| 11 | IEA *Energy and AI* (2025) cases | same, extended as a range | cite only |
| check | Global Carbon Budget; EXIOBASE 3.8.2 tables for 2015 and 2019 | AR6 database; CMIP7 *Medium* once public | ? ; ✔ CC BY-SA 4.0 |
| all | IPCC Emission Factor Database | — | ? |

EXIOBASE 3.8.2 ([Zenodo 5589597](https://zenodo.org/records/5589597)) carries tables to 2022 under CC BY-SA. Its observed series
ends in 2011; later years are estimates from trade and macro data, described there as "only
partially suitable for analyzing trends". They serve as checkpoints.

### Ruled out, or citation only

| Source | Why | |
|---|---|---|
| EXIOBASE 3.9.x | Custom non-commercial licence | ✘ |
| ScenarioMIP-CMIP7 marker scenarios, including the current-policy *Medium* | Pre-release terms: scientific use only, no sharing. Re-check on public release | ✘ for now |
| PRIMAP-hist v2.7 and later | Licence changed to CC BY-NC-SA | ✘ |
| IEA datasets (balances, ETP, WEO extended data) | Paid or no redistribution; figures citable | ? |
| IMAGE 3.2 data package (Cap et al.'s source) | Licence unchecked; the AR6 database is the open route to similar series | ? |
| OECD Environmental Outlook 2012; WIOD trends (De Koning's sources) | Superseded | — |

### Precedents

| Paper | Base table | Horizon | Scenario | Take from it |
|---|---|---|---|---|
| [De Koning et al. 2016](https://doi.org/10.1080/14693062.2014.999224) | EXIOBASE 2, 2000, four regions | 2050 | Own BAU, techno, 2 °C | The change-ratio method; constant prices |
| [Wiebe et al. 2018](https://doi.org/10.1186/s40008-018-0118-y) | EXIOBASE 3.4, 2014 | 2030 | IEA ETP 6 °C and 2 °C | Published code (FEMRIO v1); demand by regression |
| [Cap et al. 2024](https://doi.org/10.1016/j.spc.2023.12.031) | EXIOBASE 3.8.2, 2015 | 2030, 2050 | SSP1–RCP1.9 | Twelve steps and their sources; leave-one-out test |
| [Chen et al. 2022](https://doi.org/10.1038/s41597-022-01209-5) | UN and World Bank urbanisation | 2100 | All SSPs | Reference-region S-curves; hindcast; ranges. Data on Figshare |
| [Krey 2014](https://doi.org/10.1002/wene.98) | Review of energy-climate models | 2100 | — | Borrowing across model boundaries; which levers dominate when |
| [Beaufils & Wenz 2022](https://doi.org/10.1080/09535314.2021.1952404) | Any MRIO table | — | GDP and trade scenarios | SPIN: projects who trades what with whom from GDP and trade assumptions, then rebalances. It does not handle technological change, so it complements this walk; the route to changing trade structure if Milestone D needs it |
| [Springmann et al. 2018](https://doi.org/10.1038/s41586-018-0594-0) | Food-system model | 2050 | Middle-of-the-road baseline | Food baseline drivers and size; ceilings for waste (halving, 75%) and diet options |
| [Vita et al. 2019](https://doi.org/10.1016/j.ecolecon.2019.05.002), with supplement | EXIOBASE, Europe | — | Lifestyle scenarios | Worked recipes for diet, food-waste and sufficiency shocks on EXIOBASE, with re-spending rebound. For tape design more than the baseline |

To read: [Dai et al. 2024](https://doi.org/10.1080/09535314.2024.2387023) (coupling an energy model to an input-output scenario builder), the
[JRC MR-GRAS baseline](https://publications.jrc.ec.europa.eu/repository/handle/JRC120513), [Jewell & Cherp 2023](https://doi.org/10.1002/wcc.838). To obtain: [Bjelle et al. 2021](https://doi.org/10.1016/j.eneco.2021.105114), *Future changes in
consumption: the income effect on greenhouse gas emissions* (the elasticities for step 2), and
[Grubler et al. 2018](https://doi.org/10.1038/s41560-018-0172-6) (a low-energy-demand scenario).

## Decided

- **SSP2 is the storyline, not a dataset** (Nathan, 2026-11-11). Each lever is set on
  evidence in the spirit of SSP2: trends do not shift markedly from historical patterns
  ([O'Neill et al. 2017](https://doi.org/10.1016/j.gloenvcha.2015.01.004); [Riahi et al. 2017](https://doi.org/10.1016/j.gloenvcha.2016.05.009) — quote the paragraph when this plan opens).
  Published SSP2 series are the comparison. No milestone waits on a scenario dataset.

## Open for the designer

1. Confirm or rewrite the intent and success criteria.
2. Electricity built from demand and supply with fossil filling the gap (the design above).
3. Data centres: IEA base case in the baseline; its high case, and a run-on to 2050, as
   sensitivities.
4. Walk the seven game regions (minutes per snapshot), with electricity computed from country
   data before aggregating; the alternative is all 49 EXIOBASE regions.
5. The pass mark under *Checking the walk*.
6. Whether the game wants the urban and rural households.

## Milestones

A can start now; each later one builds on the one before.

- **A. Electricity-only hindcast** — first run done; see *Sprint plan* and *Milestone A results*.
- **B. Full hindcast to 2025.** Steps 1–10 and 12 on observed values; residual by sector.
- **C. To 2050.** Levers set under the SSP2 storyline; step 11 and its sensitivity. Replaces
  the constants in `engine/intensity.py` and re-bases every tape.
- **D. 2050 to 2100.** Open question: tapes re-solved at later snapshots, or scaled along the
  baseline's intensity path.

## To verify

- Global Carbon Budget's 2025 fossil CO₂ figure (about 38 Gt, unconfirmed).
- Which countries EXIOBASE puts in each rest-of-world block. `country_to_exiobase.csv` assigns
  them by continent, which is an assumption.
- Every licence marked **?**.
- The release name and licence of the IIASA SSP basic-drivers update.
- Whether [Bjelle et al. 2021](https://doi.org/10.1016/j.eneco.2021.105114)'s elasticities are published as reusable data.
