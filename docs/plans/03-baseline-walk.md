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

**Success criteria.**

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
5. **B2 Spending mix.** Elasticities from [Bjelle et al. 2021](https://doi.org/10.1016/j.eneco.2021.105114); the numbers are in the
   paper's online supplement, still to obtain. They find the effect on world emissions
   small, so a flat placeholder, marked as one in the ledger, is acceptable until then.
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

## Decided

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
4. The pass mark proposed under [Checking the walk](../design/baseline_walk.md#checking-the-walk).
5. Whether the game wants the urban and rural households.

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
