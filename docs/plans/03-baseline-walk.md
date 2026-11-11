# 03 — The baseline walk: 2011 → 2025 → 2050 → 2100

**Status: DRAFT 2026-11-11 — not yet opened.** The intent below was drafted by an assistant
from a planning conversation and has not been confirmed. Nothing here is a settled decision
until it is, and until it graduates into [`../design/assumptions.md`](../design/assumptions.md).

**Designer intent (Nathan — drafted, to confirm or rewrite).** Walk the 2011 EXIOBASE table
forward ourselves, step by named step, so that the 2050 world the game is played in rests on
explicit, sourced assumptions about how the economy's structure changes — electricity mix,
electrification, sector composition, household spending, sector carbon efficiency — rather
than on one economy-wide scalar. Check the walk against what actually happened to 2025. From
there to 2050 the **SSP2 narrative** — the "middle of the road" storyline — guides each
assumption we make ourselves; published SSP2 projections are what we compare our result
against, not an input we copy. Then carry on to 2100.

**Success criteria (drafted).**

1. A 2025 world built from the 2011 table reproduces observed emissions by major sector and in
   total, with the remaining gap reported per sector rather than hidden.
2. Every assumption is one row in a committed driver ledger: a value, a source, a licence, and
   the name of the matching IPCC scenario variable, so it can be compared with any published run.
3. A 2050 world built on SSP2-guided assumptions replaces both constants in
   `engine/intensity.py` (issue #17), and is shown beside published SSP2 runs with the
   differences explained.
4. A named sensitivity for AI data-centre electricity shows where it does and does not move
   regional and world CO₂.

**Added rigour (agent).** The hindcast-before-forecast ordering, the five-year snapshots, the
source register and its licence test, and the "one home per change" rule are the assistant's.
They serve the intent by making the walk checkable. Drop any that stop doing so.

---

## The method in one page

EXIOBASE computes emissions from three tables, so there are three things a walk can change:

- **Final demand (`Y`)** — how much is bought, and of what.
- **Recipes (`A`)** — what each industry buys to make one unit of output.
- **Emission rates (`S`, and `F_Y` for fuel households burn directly)** — emissions per unit.

Each real-world trend is assigned to **one** of those, applied in a fixed order, and the system
is re-solved. Emissions are an output. The world total is a check at the end, never a dial.

Three rules:

1. **One home per change.** A fuel saving goes into the recipe *or* the emission rate, never
   both. (The same rule the lifetimes tape follows for its `k` split.)
2. **Constant 2011 prices throughout**, as De Koning et al. 2016 and Cap et al. 2024 do. A
   physical change (TWh, vehicle-km) becomes money at the table's own implied price: the
   table's euros for that product divided by the observed physical quantity in 2011.
3. **Five-year snapshots**, each built on the one before: 2015, 2020\*, 2025, 2030 … 2050,
   then decadal to 2100. (\* 2020 is computed but never used as a checkpoint — see COVID.)

This is the method of De Koning et al. 2016, Wiebe et al. 2018 and Cap et al. 2024, applied to
the product-by-product table through `pymrio` rather than to supply-use tables. Those papers
rebalance with SUT-RAS after each step; here each step keeps column totals and the accounting
identity is asserted after it.

## The steps

Order follows Cap et al. 2024 Table 1, regrouped. "Exists" means the mechanism is already in
`src/redworlds/` for a single tape and region and needs generalising, not inventing.

| # | Step | Table | How the number is converted | Code |
|---|---|---|---|---|
| 1 | Population and income per head | `Y` | Growth ratio per region, applied to final demand | exists: `scale_final_demand` |
| 2 | Spending mix as incomes rise | `Y` | Income elasticity per product (Bjelle et al. 2021) | exists in part: per-product scaling |
| 3 | Sector shift (agriculture / industry / services) | `Y`, check on `x` | Falls out of 1–2; compared with observed value-added shares | check only |
| 4 | Electricity mix | `A`, `Y` | Generation share by source and country → move purchases between EXIOBASE's twelve `Electricity by …` products | exists: BUILD operating phase (T6) |
| 5 | Road transport electrification | `Y`, `F_Y`, `A` | EV share of fleet × cars' share of road fuel; electricity at ~⅓ the energy | exists: `apply_swap`, road `F_Y` share |
| 6 | Heating | `Y`, `F_Y`, `A` | Gas and oil to heat-pump electricity at COP ~3 | exists: `apply_swap` |
| 7 | Industry efficiency and fuel switching | `A` | Sector CO₂ pathway → fossil fuel inputs via emission factors | new |
| 8 | Aviation and shipping | `A`, `S` | Sector pathways | new, small |
| 9 | Methane and nitrous oxide | `S` | Reduction ratios for agriculture, waste, energy | new, small |
| 10 | Data centres | `A` | TWh → electricity input of *Computer and related services (72)* and *Post and telecommunication services (64)* | new, small |
| 11 | Capital | `A` | Carry the endogenised capital coefficients through consistently (backlog item) | open |

Not given a step: **urbanisation.** Gurney et al. 2021 treat it as attribution (which share of
emissions arises in cities), and Cap et al. 2024 cite a 3–7% effect on EU footprints (Ottelin
et al. 2019) and call it minor beside income. Its real effects sit inside steps 2, 5 and 6.
What *is* taken from the urbanisation literature is Chen et al. 2022's projection method:
look at reference countries that already passed today's level, step five-yearly, hindcast,
and publish slow / moderate / fast ranges.

## Checkpoints, and COVID

- **2015** — last year with observed energy data in EXIOBASE 3.8.2 (Cap et al.'s base year).
- **2019** — last year with observed GHG data in 3.8.2; pre-COVID.
- **2025** — the present; landing on observed 2025 values means whatever persisted from 2020 is
  already in.

Compare emissions, physical quantities and shares — not euros. The walk is in 2011 prices;
later EXIOBASE tables are in current prices.

2020–2021 is treated as a hump and never used as a checkpoint. With observed data to 2025 the
2020 → 2025 step is reliable on its own, so no special treatment is needed beyond that
(Nathan, 2026-11-11); the worry belonged to older papers projecting across the pandemic from
before it. Forward trends are fitted on the full observed span unless a driver's row says
otherwise. One consequence to keep: the baseline carries today's level of remote work, so the
remote-work tape's ceiling is what is left.

## Levers: making the drivers explicit

Two places where a single input series can be opened up into the things that cause it. Both
are proposed, not decided.

### Electricity: build demand and supply separately

Step 4 as written takes generation *shares* as an input. The more explicit version has no
share input at all:

- **Demand is already a result.** Steps 5, 6, 7 and 10 each raise somebody's electricity
  purchases — EVs, heat pumps, industry, data centres — and the solve adds them up. Each is a
  lever with its own row in the ledger (EV share of the fleet, heat-pump share of heating,
  data-centre TWh).
- **Supply is what gets built.** The input becomes clean generation by source and region
  (solar, wind, nuclear, hydro, in TWh, from capacity added and typical output), plus coal
  and gas retirements.
- **Fossil generation fills the gap** between demand and clean supply, within what has not
  been retired.

Why it matters: under fixed shares, extra demand from data centres or EVs is served at the
*average* mix and can never slow the fossil exit. Under the gap rule it is served by whatever
is left over, which is the only way the data-centre sensitivity can show where it does and
does not make a difference. The cost is one more assumption per region (which fossil source
fills the gap) and it stays an annual energy balance — this table has no hours, dispatch or
storage, the same limit the Smart Grid tape states.

Scenario sources that publish these levers explicitly, to assess in the register: IEA Global
EV Outlook (EV stock by scenario), IEA World Energy Outlook (capacity and generation by
source), IEA *Energy and AI* (data-centre cases), IRENA capacity statistics, and the AR6
scenario database (`Capacity|Electricity|…`, `Final Energy|Transportation|Electricity`).

### Demographics: from head-count to households

Step 1 as written is population × income per head. A ladder of more explicit versions:

- **Rung 0 — as written.** One average household per region; elasticities shift its basket.
- **Rung 1 — explicit demographic rows.** The ledger carries age structure, urban share,
  household size and income distribution per region, and steps 1–2 are derived from them:
  heating and appliances follow the number of *households*, not people; ageing moves spending
  toward health and home energy and away from commuting. Still one household column.
- **Rung 2 — household cohorts.** Split a region's household column in `Y` into groups, for
  example urban / rural × income band, each with its own basket and its own growth. Tapes can
  then act on one group — an urban and a remote track.

Rung 2 is cheap for the engine (the shock stays linear) and expensive in data: it needs
spending by group. For Europe that exists (Eurostat Household Budget Survey by degree of
urbanisation and by income quintile, the data behind Ottelin et al. 2019 and Ivanova & Wood
2020); for other regions it is patchy. Its effect on a region's *total* is small (the 3–7%
above). Its value is in what it lets a tape say about who it touches, which is a game-side
question.

Proposed: adopt Rung 1 now; let the hindcast show whether one average household misses
observed spending shifts; build Rung 2 for Region 3 only if the game wants the two tracks.

Sources to assess: Wittgenstein Centre SSP projections (population by age, sex and
education), Chen et al. 2022 (urban share), Rao et al. 2019 (income inequality under the
SSPs), Eurostat HBS, World Bank Global Consumption Database.

## Source register

**The licence test.** This repo is public and CC BY-SA 4.0. A source's *data* may be committed
(in the ledger) only if it allows redistribution and share-alike: public domain, CC0, CC BY,
CC BY-SA. A non-commercial or no-redistribution source can still be *cited* for a headline
figure, but its dataset cannot be a ledger input.

Licence column: **✔** = checked on the publisher's own page 2026-11-11; **?** = believed, not
yet checked; **✘** = checked and fails the test.

### Proposed

| Step | Observed 2011–2025 | Scenario 2026–2100 | Licence | Used by |
|---|---|---|---|---|
| 1 | UN World Population Prospects; World Bank WDI (GDP) | IIASA SSP basic drivers, 2024/25 update, SSP2 | ? ; ? ; ? | Cap (KC & Lutz 2017; Dellink 2017 — the earlier vintage) |
| 2 | National accounts household expenditure by purpose (Eurostat, OECD) as the check | Bjelle et al. 2021 elasticities | ? ; ? | Cap, Wiebe (own log-log regressions on EXIOBASE 3.4) |
| 3 | World Bank WDI value-added shares | falls out of 1–2 | ? | Cap (IMAGE 3.2) |
| 4 | Ember yearly electricity data, by country and source | to choose — see Decisions | ✔ CC BY 4.0 | Cap (IMAGE 3.2, IEA quantities for prices); Wiebe (IEA ETP 2015) |
| 5 | IEA Global EV Outlook data; fleet statistics | to choose | ? | Cap (CMIP6, Gidden et al. 2019) |
| 6 | Eurostat energy balances; heat-pump sales statistics | to choose | ? | Cap (IMAGE 3.2, CMIP6) |
| 7–9 | EDGAR sector emissions; PRIMAP-hist **v2.6** | AR6 scenario database, SSP2 runs | ? ; ✔ CC BY 4.0 (v2.6 only) ; ? | Cap (CMIP6; Frank et al. 2019 for agriculture) |
| 10 | IEA *Energy and AI* (2025) headline cases | same, extended as a range | cite only | — |
| check | Global Carbon Budget; EXIOBASE 3.8.2 tables for 2015 and 2019 | — | ? ; ✔ CC BY-SA 4.0 | — |
| all | IPCC Emission Factor Database for fuel → CO₂ | — | ? | Cap; this repo (road `F_Y`) |

EXIOBASE 3.8.2 itself (Zenodo 5589597) carries tables for every year to 2022 under the same
CC BY-SA licence. Its own description: the observed series ends in 2011; later years are
estimates from trade and macro data and are "only partially suitable for analyzing trends".
That is why they are a checkpoint here and not the base.

### Eliminated, or usable only as a citation

| Source | Why | Checked |
|---|---|---|
| EXIOBASE 3.9.x | Custom non-commercial share-alike licence, "significantly different" from 3.8 | ✘ |
| ScenarioMIP-CMIP7 marker scenarios (incl. the *Medium*, current-policy one) | Pre-release: scientific use only, no sharing with third parties. The right scenario, not yet usable. Re-check on public release | ✘ for now |
| PRIMAP-hist v2.7 and later | Licence changed to CC BY-NC-SA; pin v2.6 | ✘ |
| IEA datasets (balances, ETP, WEO extended data) | Paid or no-redistribution. Headline figures citable; Wiebe's inputs cannot be reproduced openly | ? |
| IMAGE 3.2 data package | What Cap et al. used; SSP1-specific there, licence unchecked. AR6 database is the open route to the same kind of series | ? |
| OECD Environmental Outlook 2012 projections | De Koning's GDP and population; superseded by the SSPs | n/a |
| WIOD trends | De Koning's source for efficiency trends; ends 2014 | n/a |
| A single world intensity scalar (Enerdata) | The stand-in this plan retires | n/a |

### What each cited paper did

| Paper | Base | Horizon | Scenario | Notes |
|---|---|---|---|---|
| De Koning et al. 2016 | EXIOBASE 2, year 2000, four regions | 2050 | Own BAU / techno / 2 °C | Origin of the "change ratio" method; constant prices |
| Wiebe et al. 2018 | EXIOBASE 3.4, 2014 | 2030 | IEA ETP 6 °C and 2 °C | Code on Zenodo and GitHub (FEMRIO v1); demand by regression |
| Cap et al. 2024 | EXIOBASE 3.8.2, 2015 | 2030, 2050 | SSP1–RCP1.9 | Twelve steps; leave-one-out sensitivity; five-year steps |
| Dai et al. 2024 | Australian IO + MESSAGEix | — | — | Couples an energy model to an IO scenario builder; not yet read closely |
| Chen et al. 2022 | UN / World Bank urbanisation | 2100 | All SSPs | Data on Figshare; method borrowed, driver not |

Not yet read for this plan: Beaufils & Wenz 2022 (paywalled), the JRC MR-GRAS baseline, Jewell &
Cherp 2023, and the degrowth-downscaling paper.

## Decisions for Nathan

1. ~~**Which emissions path "SSP2" means.**~~ **Decided 2026-11-11 (Nathan): the narrative
   guides, published runs are the comparison.** We set each lever ourselves, on evidence,
   in the spirit of the SSP2 storyline (trends do not shift markedly from historical
   patterns; uneven progress; no collapse, no breakthrough — O'Neill et al. 2017, Riahi et al.
   2017; quote the paragraph from the source when this plan opens). Published SSP2 series
   (AR6 database; CMIP7 *Medium* once public) are plotted beside ours and differences
   explained. Consequence: no milestone waits on a scenario dataset's licence.
2. ~~**COVID trend windows.**~~ **Settled 2026-11-11** — see Checkpoints.
3. **Data-centre baseline** — proposed: IEA base case in the baseline; the high case and a
   run-on to 2050 as sensitivities.
4. **Regional detail** — walk at the 49 EXIOBASE regions and aggregate, or walk the seven game
   regions. Proposed: seven, because it is minutes not hours, with electricity shares
   computed from country data before aggregating.
5. **Electricity as shares, or as demand and supply with fossil filling the gap** — see
   Levers. Proposed: the gap rule.
6. **How far up the demographics ladder** — see Levers. Proposed: Rung 1 now.

## Milestones

Only A can start today. B–D are listed so the shape is visible; each waits on the one before.

- **A. Electricity-only hindcast.** Apply step 4 alone from 2011 to 2015, 2019 and 2025 using
  Ember shares. Report electricity-sector and total emissions against the checkpoints. This
  tests the price conversion, the snapshot machinery and the check harness on the step whose
  code already exists.
- **B. Full hindcast to 2025.** Steps 1–9 with observed values; residual by sector.
- **C. To 2050 on SSP2-guided levers.** Replaces `engine/intensity.py`'s constants; re-bases
  every tape. Includes step 10 and its sensitivity.
- **D. 2050 to 2100.** Same machinery. Open question: tapes re-solved at later snapshots, or
  scaled along the baseline's intensity path.

## Not yet verified

- Global Carbon Budget's 2025 fossil CO₂ figure (about 38 Gt, from memory).
- Every licence marked **?** above.
- The exact release name and licence of the IIASA SSP basic-drivers update.
- Whether Bjelle et al. 2021's elasticities are published as reusable data.
