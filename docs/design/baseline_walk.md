# The baseline walk

How Red Worlds turns the 2011 EXIOBASE table into the world the game is played in: what goes
into the model, where each input lands, and how the result is checked. This is the standing
design. The work of building it is sequenced in
[`../plans/03-baseline-walk.md`](../plans/03-baseline-walk.md), which also holds the results
so far and the decisions still open; each simplification, once made, is recorded in
[`assumptions.md`](assumptions.md).

**Status, 2026-11-11.** Two steps exist and have been run as a hindcast to 2025: economy
size and electricity. Every other step is designed here and not yet built. Nothing in this document feeds a tape
number yet: the tapes still use the two scalars in `engine/intensity.py`.

**The idea in one paragraph.** Each real-world trend that changes emissions — more people,
higher incomes, a cleaner grid, electric cars — is written down as a number with a source,
assigned to the one place in the table where it acts, and applied in a fixed order. The
table is re-solved and emissions fall out. The walk runs first over years that have already
happened, so its answers can be checked against records, and then forward under the SSP2
"middle of the road" storyline.

## Where things live

The walk follows the repo's existing split: pure maths in `engine/`, anything that reads
files in `jobs/`, player actions in `actions/` (the walk adds nothing there).

| Kind | Where | Today |
|---|---|---|
| A step: world in, world out, no file access | `src/redworlds/engine/` | `economy.py`, `electricity.py` |
| Data preparation: raw download → small committed table | `src/redworlds/jobs/` | `prepare_economy.py`, `prepare_electricity.py` |
| A run: load the cached world, apply steps, report | `src/redworlds/jobs/` | `hindcast_electricity.py`, `hindcast_walk.py`, `diagnose_intensities.py`; later `walk_baseline.py` |
| Inputs: the driver ledger | `data/baseline/` | `economy.csv`, `electricity_generation.csv`, `electricity_observed.csv`; diagnostic: `intensity_outliers.csv` |
| Concordances: outside categories → EXIOBASE | `data/concordances/` | `ember_to_exiobase.csv`, `country_to_exiobase.csv` |
| Raw downloads | `data/<source>/`, gitignored | `data/ember/`, `data/worldbank/`, `data/owid/` |
| Tests, mirroring the source tree | `tests/engine/`, `tests/jobs/` | one file per module |

Commands: `just prepare-economy` and `just prepare-electricity` rebuild the committed tables
from the raw downloads; `just hindcast-electricity` runs the electricity-only walk and
`just hindcast-walk` runs both steps against observed CO₂ (each about ten minutes at seven
regions on an 8 GB laptop).

## What to read for which task

Short names link to the publisher; full citations are in
[`../references.md`](../references.md#the-baseline-walk-plan-03).

| If you are working on | Read first |
|---|---|
| The method as a whole | [De Koning et al. 2016](https://doi.org/10.1080/14693062.2014.999224) (the change-ratio method); [Cap et al. 2024](https://doi.org/10.1016/j.spc.2023.12.031) (twelve steps on EXIOBASE 3.8.2, with sources); [Wiebe et al. 2018](https://doi.org/10.1186/s40008-018-0118-y) (published code) |
| The electricity step | `engine/electricity.py`; *Electricity* below; `assumptions.md` § "The baseline walk: electricity"; [Krey 2014](https://doi.org/10.1002/wene.98) on supply against demand |
| Economy size and the SSP2 storyline | [O'Neill et al. 2017](https://doi.org/10.1016/j.gloenvcha.2015.01.004) (the narratives); [Riahi et al. 2017](https://doi.org/10.1016/j.gloenvcha.2016.05.009) (overview and quantification) |
| Spending mix | [Bjelle et al. 2021](https://doi.org/10.1016/j.eneco.2021.105114) (income elasticities on EXIOBASE); [Zhao et al. 2022](https://doi.org/10.3390/nu14224711) (food elasticities falling with income) |
| Households, age, urban and rural | [Chen et al. 2022](https://doi.org/10.1038/s41597-022-01209-5) (urban share and the reference-region method); [Ottelin et al. 2019](https://doi.org/10.1088/1748-9326/ab443d) (footprints by degree of urbanisation); [Rao et al. 2019](https://doi.org/10.1016/j.futures.2018.07.001) (income distribution) |
| Food, diet and food waste | [Springmann et al. 2018](https://doi.org/10.1038/s41586-018-0594-0) (baseline to 2050 and options); [Poore & Nemecek 2018](https://doi.org/10.1126/science.aaq0216) (impacts by product); [Vita et al. 2019](https://doi.org/10.1016/j.ecolecon.2019.05.002) and its supplement (diet shocks on EXIOBASE, with rebound) |
| Capital, technology recipes and learning curves | [Södersten et al. 2018](https://doi.org/10.1021/acs.est.8b02791); `engine/capital.py`; Wiebe et al. 2018 SI Table SI1 (capital-cost splits by technology); [Way et al. 2022](https://doi.org/10.1016/j.joule.2022.08.009) (learning rates and cost forecasts); IEA *Energy Technology Perspectives 2026* chapter 3 (the dashboards); IAEA *World Fusion Outlook 2025* for fusion |
| Trade structure | [Beaufils & Wenz 2022](https://doi.org/10.1080/09535314.2021.1952404) |
| 2050 to 2100, and what the table cannot hold | [Krey 2014](https://doi.org/10.1002/wene.98); [Grubler et al. 2018](https://doi.org/10.1038/s41560-018-0172-6) (a low-energy-demand scenario); [Kikstra et al. 2024](https://doi.org/10.1080/09535314.2023.2301443) (degrowth in integrated models) |
| Comparing a result with published scenarios | *Reference scenarios* below; IEA *Energy Technology Perspectives 2026* and *Net Zero Roadmap* (2023 update); [Van Vuuren et al. 2026](https://doi.org/10.5194/gmd-19-2627-2026) (the CMIP7 scenario set); the AR6 scenario database |

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
| 2 | Spending mix | `Y` | Income elasticity per product group, with saturation ([Bjelle et al. 2021](https://doi.org/10.1016/j.eneco.2021.105114) estimate them for 49 regions and find the effect on world emissions to 2030 small, with larger regional and product differences); age structure, household size and urban share (see Households) | per-product scaling, extend |
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
| 13 | Trade and where things are made | `A`, `Y` | Each buyer's split of a product between domestic and each foreign supplier. Observed: trade shares in EXIOBASE 3.8.2's own later tables, whose estimates rest on trade statistics. Forward: a stated SSP2 assumption per product group | new |

**Production and trade.** What each region *produces* is a result, not an input: it follows
from who demands what (steps 1–3) and who they buy it from (step 13). Until step 13 exists,
every buyer keeps its 2011 suppliers, so a region whose demand grows pulls production from
the same places it did in 2011. The shift of manufacturing between regions since 2011 is
therefore only partly captured, through faster demand growth in the regions that
industrialised, and not through changed sourcing.

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
   (the technology table printed by `just hindcast-electricity`). Since every input, capital included, is recorded per
   euro of output, the inputs behind a kWh of solar vary by the same factor, and in most
   regions are far too small. Sprint item A5 in the plan replaces such a technology's recipe with a
   borrowed one. Updating that recipe from 2011 costs to current ones is then a separate
   lever, and is where assumptions about 2050 construction costs and efficiencies enter.
3. **Decide on the 2011 construction trough** at the first snapshot (see the backlog
   diagnostic under *BUILD capex (a)*).

## Technology maturity

A technology is not one fixed recipe. Solar, wind and batteries get cheaper as more are
built; a technology not yet commercial, such as fusion, has no observed recipe at all. Each
technology the walk treats explicitly gets a **technology card** in the ledger, laid out
like the dashboards in the IEA's *Energy Technology Perspectives 2026* (chapter 3), which
describe each technology under three headings: its market, its competitiveness, and what
enables or holds it back.

**Market status**, in the IEA's five categories:

| Status | Meaning | Examples in ETP 2026 |
|---|---|---|
| Pre-commercial | Not yet in commercial operation | Small modular reactors; fusion earlier still |
| Awaiting adoption | Proven, struggling to be deployed | |
| Building momentum | In some markets, global effect limited | |
| Strong growth | Widely adopted, share growing | |
| Consolidation | Widely adopted, share stable or falling | Large reactors |

The status decides how a technology's future is written down:

- **Strong growth or consolidation: a learning curve.** Cost falls as a power of cumulative
  production (Wright's law): each doubling of what has been built cuts cost by a fixed
  share. [Way et al. 2022](https://doi.org/10.1016/j.joule.2022.08.009) fit this to history and test it by backcasting on more than 50
  technologies. Their experience exponents, and the cost fall per doubling they imply:

  | Technology | Exponent | Cost fall per doubling | Stated life |
  |---|---|---|---|
  | Solar PV electricity | 0.319 ± 0.043 | 20% | 30 y |
  | Wind electricity | 0.194 ± 0.041 | 13% | 30 y |
  | Lithium-ion batteries | 0.421 ± 0.063 | 25% | 12 y |
  | Electrolysers | 0.129 ± 0.067 | 9% | 16 y (table S24 gives 10) |
  | Nuclear, hydro | 0.00 | none | 40 y, 100 y |
  | Biopower | 0.05 | 3% | 30 y |

  Two things follow for the walk. Cost is **conditional on deployment**: the curve gives a
  cost only once the ledger says how much is built, so "what was built when" is the lever
  and cost is its consequence. And the fit comes with an error, which gives the slow,
  moderate and fast variants without inventing them.
- **Building momentum or awaiting adoption: a curve with a wider range**, and the IEA
  scenarios' deployment figures as the comparison.
- **Pre-commercial: a published range, labelled as borrowed.** The IEA puts fusion among
  technologies whose "viability remains unproven" and judges such technologies unlikely to
  reach significant market shares within a decade. The IAEA's *World Fusion Outlook 2025*
  includes global deployment modelling by MIT, in which fusion's share of electricity in
  2100 runs from about a tenth to about a half as the assumed capital cost in 2050 falls
  from roughly USD 11,300 to USD 2,800 per kW (from summaries of the report; confirm in the
  report). The baseline carries no fusion unless a ledger row says so; a fusion tape
  carries the range as its uncertainty.

**The walk runs to 2100, so a pre-commercial technology still needs a path.** "Not within a
decade" leaves seventy years. For each such technology the ledger holds three things, all
assumptions and all marked as such: an invented recipe (what a unit needs and emits, built
from the nearest existing technology — fusion from nuclear, with a stated cost multiple);
a year of first commercial deployment; and a deployment path after it, with a central case
and a range. The central case goes in the baseline. The range is what the sensitivity
report varies, so the weight of "how soon does fusion work" can be set beside, say, "how
large do data centres grow".

**From a curve to a recipe.** Three sets of ledger rows per technology:

- *Cost and performance by build year*: installed cost per kW, capacity factor, operating
  cost and lifetime for a unit built in a given year.
- *What was built when*: capacity added by year and region, observed and then assumed.
- *A fleet recipe per snapshot*: the fleet standing in a snapshot year is a mix of build
  years, so its inputs per kWh are the average over units still in service, weighted by
  output. A 2025 solar fleet is mostly recent, cheap units; a 2025 nuclear fleet is mostly
  old ones.

The cost breakdown that turns a cost per kW into purchases from particular products is
[Wiebe et al. 2018](https://doi.org/10.1186/s40008-018-0118-y) SI Table SI1. A tape that builds something in the game's 2050 reads the
same curve at 2050 and later: the baseline and the tapes share one description of each
technology.

## Recipe or concordance

A tape or a step can describe a technology in two ways.

- **A concordance** maps the technology onto products the table already has, with shares:
  "an electric car is 60% *Motor vehicles*, 30% *Electrical machinery*, 10% other". It
  changes how much of existing products is bought. It is cheap, and it inherits whatever
  the table says about those products.
- **A recipe** is a column of its own: what one unit of output needs from every other
  product, and what it emits. It is needed when the table has no usable description.

Use a concordance unless all three of these hold:

1. **No reliable column exists.** The product is absent from the table, or fails the
   reliability check in that region (next section).
2. **Its own supply chain or emissions are the point.** A heat pump is a manufactured
   appliance; the table's machinery products describe making one well enough, and what
   matters is the electricity it uses. A fusion plant, a hydrogen electrolyser or a
   near-zero steel mill produces something whose inputs and emissions differ from anything
   in the table.
3. **It gets big.** It reaches more than about one per cent of its market within the
   horizon. Below that a stand-in costs little accuracy.

On that test, recipes are needed for solar PV and wind (no reliable column in most
regions), for fusion and small modular reactors, and later for hydrogen, near-zero steel
and cement, and carbon removal. Concordances serve for electric vehicles, heat pumps,
insulation, appliances and every REDUCE basket. The seventeen technologies with dashboards
in the IEA's *Energy Technology Perspectives 2026* are the checklist of what might be large
enough to need one.

## Which regions can describe which products

The table describes every product in every region, including products a region barely
makes. `just diagnose-intensities` compares each region's direct greenhouse-gas intensity
for each product with the output-weighted world intensity, and lists the cells more than
five times above or below it in `data/baseline/intensity_outliers.csv`.

At seven regions, of 1,247 region-product cells with output:

| | Cells | Share of world emissions |
|---|---|---|
| Far from the world intensity, and under 1% of world output (likely artefacts) | 41 | 0.1% |
| Far from the world intensity, on a larger share of output | 110 | 4.1% |

- **The artefacts are few and small today.** They matter only when something scales them
  up, which is why the electricity step tests each technology before using it.
- **They cluster.** South Asia holds 24 of the 41; Europe and Central Asia holds none.
  Electricity products account for eleven, nearly all solar, geothermal and tidal.
- **The 110 larger cells need reading one by one.** Some are real (landfill in Africa and
  Middle East, cattle in South Asia); some look like booking differences (gas distribution
  in Mainland East Asia at six times the world intensity).
- **Aggregation hides more.** Seven regions average away country-level oddities; the same
  check on the 49-region table will find more, and belongs with the work on Region 3's
  heat-and-power plants.
- **A caution on reading it.** The comparison is with the world average, so where the
  largest producer is itself the odd one, everyone else is flagged instead. Geothermal is
  the example: Region 3's high figure dominates the average.

Rule for tapes and steps: before scaling a product in a region, look it up in this list. A
flagged cell needs a stand-in, a borrowed recipe or a stated reason to trust it.

## Reference scenarios

The walk's own assumptions follow the SSP2 storyline. To judge them, and to give the tapes
something to be measured against, each lever is set beside three scenarios the IEA
publishes and maintains (definitions from *Energy Technology Perspectives 2026* and the
IEA's scenario documentation for the World Energy Outlook 2025):

| Scenario | Kind | What it assumes | Role here |
|---|---|---|---|
| Current Policies (CPS) | Exploratory | No change in energy policy beyond what is already in law and regulation | Lower bound for the baseline's clean-technology levers |
| Stated Policies (STEPS) | Exploratory | Current policies plus those announced or in advanced planning; aspirational goals are not assumed met | The baseline's closest published neighbour |
| Net Zero Emissions by 2050 (NZE) | Normative | A pathway for the energy sector to reach net zero CO₂ by 2050, with no offsets from other sectors | The benchmark a set of tapes is measured against |

**The default rule:** a technology's growth in the baseline follows the Current Policies
Scenario. A ledger row may depart from it only by stating the exception and its reason. A tape's
ceiling can be read against NZE: the IEA's *Net Zero Roadmap* (2023 update) gives milestones
of the kind a tape describes — renewable capacity tripled to 11,000 GW by 2030, electric
cars at two-thirds of new sales by 2030, energy-sector methane cut by 75% by 2030, coal
demand down from about 5,800 to 3,250 Mtce by 2030 — and attributes about 35% of the
emission reductions needed by 2050 to technologies not yet on the market.

Two cautions. The NZE scenario is revised each year, and the 2025 version is described by
the IEA as no longer a limited-overshoot pathway, so a milestone is cited with its edition.
And all IEA scenarios share one population and GDP path, so the difference between them is
policy and technology only — which is what makes them a clean comparison for the tapes.

**A second lens, so the first does not become the frame.** The IEA's scenarios describe
change led by industry and policy, with the services people enjoy held roughly constant:
more is built, and what is used is swapped for a cleaner version. That is the outlook of
the BUILD wing and of most SWAP tapes, and it is the right reference for them. It says
little about using less. The counterweight is the method of MacKay's *Sustainable Energy —
Without the Hot Air*, already the basis of every tape ceiling in this repo: set economics
and acceptability aside, and ask what is physically required and physically possible per
person. Each technology card therefore carries two readings where both exist: what the IEA
scenarios deploy, and what the physical arithmetic allows or demands. Where they disagree,
the disagreement is recorded, not resolved in favour of either.

**What may be used.** IEA reports — text, figures, and numbers read from them — are
published under CC BY 4.0 and can be cited and adapted with attribution. IEA datasets, data
explorers and the data annexes to its reports are not: they may be quoted only in
insubstantial amounts and never redistributed. So a ledger row can cite a figure from an
IEA report; it cannot be filled from an IEA data file. (IEA terms of use, read 2026-11-12.)

## Prices are an input

The table holds money; almost everything the walk and the tapes say is physical — TWh
built, vehicle-km avoided, tonnes of steel. Every such statement enters through a price, so
the price is part of the assumption and is stated, not left implicit.

- **One price table**, in the ledger: money per physical unit by product, region and year,
  with a source or a derivation for each row.
- **Used by both the walk and the tapes.** A tape that builds 80 TWh of nuclear and
  displaces 80 TWh of fossil generation converts each at its own price from the same table.
- **It can differ by tape and by year.** A tape may reach its money a different way — a
  capital cost per kW for a BUILD, a price per litre for a fuel SWAP — and a 2050 price need
  not be a 2011 price. What is fixed is that the conversion is written down.

Today prices are derived from the 2011 table as money output over physical supply
(`engine.electricity.implied_prices`). That derivation is the default row, and it is
visibly wrong in places: where a product's physical supply is under-recorded, as for Region
3's electricity, its price is overstated.

## How the walk is built to be re-run

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

The input-output walks this design follows stop at 2050. For 2050–2100 the walk carries fewer
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
| 11 | IEA *Energy and AI* (2025) cases | same, extended as a range | figures from the report, CC BY 4.0 ✔ |
| 12 | IRENA installed costs; capacity added by year (Ember, IRENA) | [Way et al. 2022](https://doi.org/10.1016/j.joule.2022.08.009) learning rates (CC BY ✔); IEA *Energy Technology Perspectives 2026* dashboards (CC BY 4.0 ✔) | ? for IRENA |
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
| IEA datasets, data explorers and report data annexes | Not under the reports' CC BY licence: insubstantial amounts only, no redistribution. Figures in the reports themselves are CC BY 4.0 and citable | ✘ |
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

Read only in part so far: [Dai et al. 2024](https://doi.org/10.1080/09535314.2024.2387023), [Jewell & Cherp 2023](https://doi.org/10.1002/wcc.838), [Grubler et al. 2018](https://doi.org/10.1038/s41560-018-0172-6)
and the [JRC MR-GRAS baseline](https://publications.jrc.ec.europa.eu/repository/handle/JRC120513). The supplement to [Bjelle et al. 2021](https://doi.org/10.1016/j.eneco.2021.105114) is in hand: a mapping of EXIOBASE's 200 products to
its consumption categories, six region groups, and projected spending shares by category to
2030, which is what step 2 needs.
