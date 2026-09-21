# Backlog

The informal working backlog for Red Worlds. Two tiers:

- **This file** holds direction, sequencing, and open modelling decisions: things that need
  thinking or a model run before they are implementable.
- **GitHub issues** hold implementable units: one function, one test file, a clear done
  condition. When an item here becomes that shaped, promote it to an issue and link it.

Dated entries, newest at the top of each section. Strike or move items rather than deleting
them, so the reasoning trail survives.

---

## Sequencing (MVP path)

The MVP the game needs is a stateless function: one 2050 baseline world, one shock, one
Leontief solve, a deployment curve, a 50-year cumulative delta. See
`docs/design/red_carbon_contract.md` §7. Order of work:

1. [x] ~~Rewrite `docs/design/game_mechanics.md`, `docs/design/assumptions.md` and
       `examples/prompts/red_worlds_context.md` to the 2050 tape contract.~~ Done 2026-09-16,
       together with `architecture.md`, the READMEs and CLAUDE.md.
2. [x] ~~`load_config()` — GitHub issue #5.~~ Done 2026-09-17 (`tests/test_config.py`;
       the `exiobase_mrio` integration fixture is now live).
3. [x] ~~`scale_final_demand()` and `get_sector_emissions()`. First REDUCE runs end to end
       on `pymrio.load_test()`.~~ Done 2026-09-17, with `get_region_emissions()`,
       `recalculate_from_final_demand()` (Y-side path, reuses L) and `apply_reduce()`
       (issue #8). Emissions are consumption-based (`D_cba`).
4. [x] ~~A test-world concordance fixture under `tests/fixtures/` so region aggregation gets
       real unit tests.~~ Done 2026-09-16 (`tests/fixtures/test_world_regions.csv`; the
       `exiobase_mrio` integration fixture also exists now). Scenario-mapping fixture still to do.
5. [x] ~~Validate `region_mapping.csv` against the real EXIOBASE 3.8.2 download (integration
       test); settle Taiwan (CSV says region 7, game design says 6).~~ Done 2026-09-17:
       Taiwan is region 6 per the game's regions doc; integration test checks the CSV's
       codes equal the table's.
6. [ ] `jobs/build_baseline.py` stub: 2011 EXIOBASE → capital endogenised → SSP2 2050
       world → 2050–2100 trajectory. First check the capital-flow data resolution (see
       Modelling decisions).
7. [ ] `score_tape()` composition returning the result shape in the contract doc §4.3.
8. [x] ~~First empirical notebook: "what does a 0.5% cut in Region 3 household demand do to
       cumulative CO2 2050–2100?" This is the moment outsiders can use the repo.~~ Done
       2026-09-17 on the 2011 table (`examples/03_first_reduce_number.ipynb`): a 1% cut
       is −59 Mt/yr, one brick ≈ 0.33% at flat deployment. Re-run once the 2050
       baseline exists.
9. [x] ~~Fix stub TODO issue numbers (issue #10) and merge the two references files.~~ Done
       2026-09-16 for the five issues that exist (#5–#9). The engine primitives, `capital.py`,
       `scoring.py` and `build_baseline.py` have no issues yet (issue #10 assumed #11–#15,
       which Dependabot took): their TODOs point here.
10. [x] ~~Create GitHub issues for the stubs without one.~~ Done 2026-09-21. Every
       `TODO: implement` in `src/` now names a real issue: #15 `rebalance_economy`,
       #16 `shift_sector_share`, #17 the SSP2 walk (replacing `intensity.py`'s two
       stand-in scalars and finishing `build_baseline`), #18 `update_scenarios`.
       #5 `load_config` and #8 `apply_reduce` closed as shipped.

Phase 2, not on the MVP path: per-player worlds, the shared job queue, multi-tape
interaction, nightly growth.

---

## Beta Day tape table (the game's next epic, 2026-09-18)

The game's next playtest scores real tapes from **a precomputed table** produced here, not
from a live worker: the per-play inputs are tape id, outcome fraction and push level, and
Y-side shocks are linear in the fraction, so each tape's solve runs once and ships as JSON.
The queue/worker design in `architecture.md` is unchanged and becomes necessary only when
tapes must interact. Contract: `docs/design/red_carbon_contract.md` §4.4.

- [ ] **T1 Cache the aggregated baseline.** `jobs/build_baseline.py` for now means: load
      2011 pxp → `aggregate_regions` → `endogenise_capital` → `calc_all` → persist to
      `data/worlds/baseline_2011_agg7/`; add `just baseline`. *Done when:* a second process
      loads it in seconds and `total_emissions` matches notebook 03 (44.5 Gt). The SSP2
      walk stays a TODO in the docstring, not a stub in the way.
- [ ] **T2 Populate the tape records and the concordance.** `data/tech_choices/options.toml`
      and `data/concordances/exiobase_to_scenario.csv` are placeholders. One record per game
      tape (`eca_nuclear`, `eca_geothermal`, `eca_fusion`, `eca_electric_vehicle_transition`,
      `eca_smart_grid`, `eca_ban_gas_supply`, `eca_extended_product_lifetimes`, `eca_buy_less`,
      `eca_remote_work_commuters`) with the contract §4.2 fields plus a `beta_day_assumption`
      text field. Baskets use exact `products.txt` labels. Each record also carries
      `regional_ceiling` — the physical maximum for that intervention in the region
      (land, resource or behavioural, MacKay-style) — from which the game derives how
      many copies of the tape exist. *Done when:* a loader validates every product in
      every basket against the aggregated table's index, and every record has a
      ceiling with its basis stated.
- [ ] **T3 REDUCE tapes through the existing path.** `apply_reduce` works; the three REDUCE
      tapes need their baskets (T2) and, for the commuting tape, the direct-household
      emissions fix (scale the `F_Y` row by the fuel product's own change — see Open).
- [x] **T4 Consumer-side SWAP.** `apply_swap`: cut product A in the region's household
      column by `pct_rollout`; add product B at the tape's service-equivalent (COP 3 for gas
      → heat-pump electricity; ~⅓ energy for petrol → EV electricity), priced; re-spend the
      remainder flat across the household basket via `rebalance_economy` (flat weighting,
      as sanctioned above). *Done when:* `gdp_impact` ≈ 0 for a SWAP (the closed-budget check).
- [x] **T5 BUILD, construction phase.** GFCF injection in the region across *Construction
      work (45)* 40%, *Machinery and equipment n.e.c. (29)* 42%, *Electrical machinery (31)*
      9%, *Other business services (74)* 9% (Wood/Wiebe 2018 SI1), spread over `build_years`.
      Injection, with the reallocation flag exposed but off. Returns the construction-phase
      annual delta (positive). *Done when:* nuclear's construction total is a few percent of
      its operating abatement.
- [x] **T6 BUILD, operating phase — A-matrix mix change.** Decided 2026-09-18 (game): for
      every region-3 column of `A` (and the region's `Y` columns), move the fossil
      electricity input coefficients (*Electricity by coal / gas / petroleum*) to the built
      product (*Electricity by nuclear* / *by Geothermal*) sized to the tape's TWh at the
      table's basic price, keeping each column total; re-invert `L`; rescale nothing in `S`
      (the target product's own intensity row already exists). Wiebe et al. 2018 §3.3. A
      Y-only substitution is a cross-check, not the method — industrial electricity sits
      in `Z`. Returns the operating-phase annual delta (negative). *Done when:* nuclear lands
      in the contract's 0.5–1.8 Gt range at the 10-reactor cover.
- [ ] **T7 Grid tape. Hold — the tape's design is under review on the game side.** Two
      candidate mechanisms, needing different shocks, so building either first risks
      throwing the work away:
      *(a) efficiency* — a coefficient cut on *Transmission services of electricity* and
      *Distribution and trade services of electricity* own-use inputs (losses 6–8% → ~4%),
      optionally a 2–3% demand-response cut on every sector's electricity inputs; one full
      solve. This is the version the "enabler" hypothesis in the Modelling decisions section
      describes, and the one this repo has doubted since it was written, because curtailment
      is not in the table and the remainder is a few percent of a service sector.
      *(b) distributed generation* — a shift of the region's generation mix toward
      *Electricity by solar photovoltaic* at small scale, **plus** reduced transmission and
      distribution service consumed per kWh delivered, **plus** a capital-mix change toward
      electrical machinery and away from heavy construction. This carries a real
      generation-mix change, so it has a far more plausible route to a brick.
      *Magnitudes, checked 2026-09-18 — both framings clear a brick, so this tape is not
      blocked on being too small:* EU curtailment runs ~30 TWh/yr for want of transmission
      capacity and ~72 TWh/yr including all bottlenecks (2024), at only ~50% renewable
      share, and rises steeply with penetration — recovering ~100 TWh/yr at ~300 g/kWh
      marginal is ~30 Mt/yr, ~1.5 Gt over the window. T&D losses are ~6.2% of output in the
      EU and materially higher across the rest of region 3 (Turkey ~9.5%, parts of the
      Balkans and Central Asia far higher), so two points saved on ~6,000 TWh is ~120 TWh/yr,
      ~0.9 Gt at a 2050 average intensity. The regional point matters: this tape is worth
      more in region 3 than an EU-only reading suggests, because region 3 contains the grids
      with the most headroom.
      *Note on method:* this model has no capacity constraints, no dispatch and no time
      resolution, so an "enabling" effect cannot be derived here — demand for wind
      electricity is always met. The coefficient change must be **imposed exogenously** and
      cited, as Wiebe et al. 2018 impose IEA ETP scenario coefficients. Sources: CEER Report
      on Power Losses; World Bank T&D loss series; EU congestion and curtailment reporting.
      *Blocked on:* the game confirming which. Ask before building. Whichever lands, the
      standing question — can a distribution-sector coefficient shock score competitively
      against a direct tape? — is worth answering for (a) even if (b) is adopted, because it
      is the general question about enabling infrastructure in an MRIO.
- [x] **T8 Fusion.** Nuclear's mechanics with `build_years_reference` 20 and 2× capex per GW;
      the table gets one honest number, the game's outcome band carries the maturity story.
- [x] **T9 The export job.** `jobs/export_tape_table.py` (notebook 04 first if faster):
      for each record, run from the cached baseline and write `data/exports/tape_table_<date>.json`
      — per tape `annual_delta_construction`, `annual_delta_operating`, `gdp_impact_full`,
      `build_years_reference`, `deployment_curve`, `cover_magnitude`, `cumulative_full_flat`,
      `provenance`, `regional_ceiling` and `copies` (ceiling ÷ brick, floored);
      file-level `baseline`, `intensity_scalar_2050`, `units`. For BUILD (T6 is
      non-linear) also store deltas at deployment 0.25 / 0.5 / 0.75. A JSON schema beside it;
      `just export-tapes` regenerates byte-identically. *Done when:* all nine tapes export.
- [x] **T10 Docs.** `assumptions.md`: the 2011 → 2050 intensity scalar (0.6 working, source
      to cite) and the Beta Day simplifications; `game_mechanics.md`: the table shape;
      close the "GitHub issues for stubs" item above while there.

---

## Modelling decisions

Each of these changes a number the game shows. Sources and working numbers are in
`docs/design/red_carbon_contract.md`. Decided items stay here, struck, so the reasoning
trail survives.

### Decided

- [x] ~~**REDUCE rebound, factor of two.**~~ **Decided 2026-09-16 (Nathan): REDUCE reduces
      total spend (GDP) with no rebound, at least for now.** RE2 stands; the 2026-08-06
      "halved for re-spending rebound" sizing is withdrawn. This is a structural feature of
      the wings: BUILD moves money, SWAP keeps it, REDUCE removes it. *Owed on the game
      side:* a decisions-log entry, and re-sizing the REDUCE covers that still carry the
      halving (Make Stuff Last, Remote Work). Use Less Stuff was already corrected to 0.5%.
- [x] ~~**2050 baseline: which SSP.**~~ **Decided 2026-09-16: SSP2.** How to get there from
      2011 is still a to-do (see Sequencing step 6). Precedents: Cap et al. 2024 (SSP1 on
      EXIOBASE 3.8.2), Wiebe et al. 2018 (IEA ETP to 2030, code on Zenodo).
- [x] ~~**Construction-sector footprint multiplier.**~~ **Resolved to a to-do 2026-09-16.**
      Not an assumption once the model runs: it is the footprint intensity of the products
      the capex is injected into, weighted by the split. Adopt Wood/Wiebe 2018 SI Table SI1
      shares per technology (nuclear: 42% machinery, 40% construction, 9% electrical
      machinery, 9% other business services), run for Region 3, read off the number.
      Refine later with per-region splits and explicit steel/cement content.

### Emissions accounting — which rows to read, and the two traps

**Verified against the real 2011 pxp tables, 2026-09-18.** Recorded here because it is the
kind of thing that is invisible until a number is wrong by a factor of a million.

**The rule: read one pre-characterised row. Never sum rows.** EXIOBASE's `impacts` extension
is not a set of disjoint stressors — it contains the same emissions several times over, in
different characterisations and at different levels of aggregation:

- `Carbon dioxide (CO2) IPCC categories 1 to 4 and 6 to 7 (excl LULUCF)` and
  `Carbon dioxide (CO2) CO2EQ IPCC categories ...` are **the same number** (CO2's GWP is 1).
- `Carbon dioxide (CO2) Fuel combustion and cement` and `Carbon dioxide (CO2) Fuel combustion`
  are **nested subsets** of it.
- There are at least six GHG GWP variants — CML 2001 baseline, CML 1999 baseline, GWP20,
  GWP500, and net GWP100 min/max — which are the same emissions re-characterised.

So anything of the form "sum every row whose label contains CO2" multiply-counts. The rows to
use, both already pre-aggregated:

| Quantity | Extension | Row | Unit |
|---|---|---|---|
| All-GHG | `impacts` | `GHG emissions (GWP100) \| Problem oriented approach: baseline (CML, 2001) \| GWP100 (IPCC, 2007)` | **kg CO2 eq.** |
| CO2 only | `impacts` | `Carbon dioxide (CO2) IPCC categories 1 to 4 and 6 to 7 (excl land use, land use change and forestry)` | **Gg** |

⚠ **Trap 1 — the units differ by 10⁶.** The GHG row is in **kg CO2 eq**; the CO2 row is in
**Gg** (10⁶ kg). Adding a CO2 field by copying the GHG read path gives an answer a million
times out, and at these magnitudes that can still look superficially plausible. Read
`impacts/unit.txt` per row rather than assuming.

⚠ **Trap 2 — `F_Y` is not optional.** Industry emissions (`F`) are 39.4 Gt CO2e; direct
household emissions (`F_Y`) are another 5.1. The world total only reconciles with both.

**Reconciliation, world 2011, F + F_Y:**

| | Value | Cross-check |
|---|---|---|
| All-GHG | **44.5 Gt CO2e** | matches `examples/03_first_reduce_number.ipynb` |
| CO2 only | **32.5 Gt CO2** | real-world 2011 fossil + cement is ~34 Gt |
| CO2 share of CO2e | **73%** | — |

The CO2 share is global; it will differ by region and by tape, which is the argument for
carrying both fields per tape in the export rather than applying one global fraction.

**Two assumptions this bakes in, for `assumptions.md`:** the totals **exclude LULUCF** (it is
in the row name), and the GWPs are **IPCC 2007 (AR4)** via CML 2001, not AR5 or AR6. Both are
defensible and neither is the current convention, so both should be stated once rather than
discovered later.

**Known oddity, not ours:** pymrio issue #72 reports surprising GHG intensities in EXIOBASE 3
for solar photovoltaic and geothermal electricity. Both are Beta Day tape technologies, so
check those two sectors' coefficients explicitly at T5/T6 before trusting a BUILD result.

### Open

- [x] ~~**Direct household emissions under a REDUCE.**~~ Done 2026-09-21. pymrio recomputes `F_Y` from `S_Y`,
      which is normalised per final-demand *column* total, so cutting one product's demand
      scales a region's direct household emissions (fuel burnt in cars and boilers) by the
      change in total household spend, not by the change in that product. Right for a
      broad basket, wrong for a vehicle-fuel or gas tape, where `F_Y` should track the fuel
      row. The action now scales only a named share of `F_Y` by the fuel product's own
      change; the remaining direct emissions stay fixed.
      **Confirmed in scope 2026-09-18 (Nathan): do it in T3, not later.** Two Beta Day
      tapes are exactly this case — the remote-work tape cuts vehicle fuel and the gas tape
      cuts household gas — so the broad-basket approximation is wrong for both, and `F_Y` is
      11% of the world total (5.1 of 44.5 Gt CO2e), not a rounding error. Region 3's 32.9%
      road share comes from `Energy Carrier Net TROA / Total`; gas uses the tape's gross
      physical heating anchor. Both records are provisional because these are apportionment
      proxies rather than fuel-resolved characterised emissions.
- [x] ~~**Carry CO2 as well as CO2e through to the export.**~~ Done 2026-09-21. The game converts cumulative
      emissions to a 2100 temperature reading, and that conversion (the transient climate
      response to cumulative emissions) is defined on **CO2 alone** — CO2e hides the
      difference between a permanent gas and a decade-lived one, so two tapes with equal
      CO2e can have unequal consequences for 2100. Cheap to fix, because EXIOBASE already
      publishes both as pre-characterised rows in the `impacts` extension. See **Emissions
      accounting** below for the row names and the unit trap. Decided in scope 2026-09-18;
      do it in T9 so the export schema is right first time.

- [ ] **GDP impact attribution.** `gdp_impact` books the world total of final demand
      removed. A Region 3 cut in imported goods also lowers value added abroad; per-region
      attribution needs the `Value Added` factor input through the Leontief solve
      (`D_pba` of value added by region). Do it when the game shows GDP per region.

- [x] ~~**BUILD capex (a): is capital endogenous?**~~ **Decided 2026-09-16 (Nathan):
      endogenise capital from the start, as a `build_baseline` step.** Method: Södersten,
      Wood & Hertwich 2018: move the depreciation-based capital-goods flow from the GFCF
      column into the coefficient matrix, leaving net expansion in Y. Why now: it is a
      one-time baseline operation, and it makes every consumer-demand tape (SWAP, REDUCE)
      carry its capital consequences automatically (less computer demand → less factory
      capital; more electricity → more grid and generation capital), and it captures
      renewables' in-window replacement cycles without special-casing. Construction stays
      a normal product; it just also appears as an input of every capital-using sector.
      *Consequences:* the BUILD hump still needs an explicit GFCF injection during the
      build years because endogenised capital is proportional to output and a plant under
      construction produces nothing; the operating-years capital charge then overcounts a
      long-lived new plant a little (roughly the hump spread over 40 years, small against
      displacement, consistent with the baseline's treatment of every other plant).
      **MVP decision 2026-09-21: keep that steady-state charge.** The cached `A` matrix does
      not retain the capital component separately, so an exact net-out is unavailable and
      a guessed one would treat new plants unlike the baseline. Revisit only with stored
      capital coefficients or a cohort model. The REDUCE "non-capital Y" basket excludes
      only the remaining net-investment column. *Checks before building:*
      - [x] ~~Confirm the published capital-flow matrices exist at this repo's resolution.~~
            Confirmed 2026-09-16: Zenodo record 7073276 (Wood & Södersten) has pxp and ixi
            files for 1995–2020, CC-BY-4.0; the file is `Kbar_exio_v3_8_2_2011_cfc_pxp.mat`
            (flow form, MEUR; coefficient form is Kbar · x̂⁻¹). Reading `.mat` needs scipy
            (add as a dependency when implementing `load_capital_use`).
      - [x] ~~Implement `load_capital_use` and `endogenise_capital`.~~ Done 2026-09-17.
            On the real 2011 pxp table Kbar totals 8.90 T EUR against 13.04 T EUR of
            GFCF (68%). After subtraction, 6,363 of 480,200 GFCF cells go negative,
            summing to −2.25 T EUR: net investment is negative wherever a region's
            industries consumed more of a capital good (from a given supplier region)
            than the region's GFCF column bought from that supplier. Left as it falls
            for now, so the accounting identity holds.
      - [x] ~~Decide what to do with negative net-investment cells.~~ **Decided
            2026-09-18 (Nathan): keep them**, as Södersten et al. do — net investment is a
            residual and the accounting identity holds. Still run the diagnostic inside T1
            (how much of the −2.25 T is supplier-region trade mismatch versus genuine
            same-region disinvestment) and record it; revisit only if it is mostly the
            latter, which would mean the subtraction is saying something about capital
            stocks rather than about trade.
      - [x] ~~Diagnostic, run in T1 2026-09-19.~~ **It is mostly the latter, and the
            decision still holds — for a different reason than the one it was made on.**
            At EXIOBASE's own 49 regions, of the −2.25 T EUR across 6,363 cells:

            | | Cells | Value |
            |---|---|---|
            | same-country (genuine disinvestment) | 361 | **−2.03 T EUR (90%)** |
            | cross-country (trade mismatch) | 6,002 | −0.22 T EUR (10%) |

            So trade mismatch is almost all of the *cells* and almost none of the *value*.
            The value is concentrated: the US alone is −1.00 T (44% of the total) and
            *Construction work (45)* is the largest cell in nearly every affected country
            (US −704 bn, BR −103 bn, RU −90 bn, MX −82 bn, DE −63 bn).

            That pattern is not an artefact — it is 2011. Consumption of fixed capital on
            structures is large and steady because it depreciates a stock accumulated over
            decades, while gross investment in construction collapsed after 2008 and had
            not recovered by 2011. A negative net investment in US structures in 2011 is
            the table correctly reporting that the US was running its building stock down
            that year. Keeping it is right: clipping it would invent investment that did
            not happen, and the identity would break.

            **What it does mean** is that the 2011 basis is a construction trough, and two
            things downstream touch exactly that cell. (a) The SSP2 walk (5b) is where a
            trough year should be normalised, if it is going to be — worth an explicit
            decision there rather than inheriting 2011 silently. (b) T5 injects BUILD capex
            into *Construction work (45)*, whose baseline net investment is negative in the
            anchor year; the injection is a delta against baseline so the arithmetic is
            unaffected, but the J-curve story is told against an unusually depressed base.
            Neither blocks sprint 2.

            *Caveat on method:* the diagnostic in `jobs/build_baseline.py` runs on the
            aggregated world, where "same region" means same *game* region and so counts
            DE→FR as domestic. It reported 96% same-region against the true 90%, close
            enough to be a usable smoke test but not the number to quote. The 49-region
            figures above come from the unaggregated table (the GFCF subtraction alone —
            no Leontief inversion needed, so it is a cheap check to repeat).
      - [ ] Carry the capital coefficients through the 2011 → 2050 extrapolation
            consistently.
      - [ ] Runtime: the full-system integration test (parse, invert, endogenise,
            re-invert 9800 × 9800) takes ~19 min and 2.9 GB peak on an 8 GB laptop.
            Fine for a one-off baseline build; cache the result, never run per tape.
- [x] ~~**BUILD capex (b): where does the money come from?**~~ **Decided 2026-09-18
      (Nathan): injection.** New money, GDP rises, strongest J-curve; matches BU1 and Wiebe
      et al. 2018. The construction phase is a GFCF injection into construction (45),
      machinery n.e.c. (29), electrical machinery (31) and other business services (74) on
      the Wood/Södersten SI1 split; the operating phase is a separate A-matrix mix change
      (T6). The alternative considered was reallocation within the remaining GFCF column
      (GDP-neutral, crowds out other investment, softens the hump). **Keep the reallocation
      flag on `rebalance_economy` exposed but off**, so the cross-check stays cheap.
- [ ] **BUILD phase two: post-build technology mix.** The genuinely hard half of BUILD:
      after the build years, change the electricity sector's coefficient column (more
      nuclear/geothermal product, less coal/gas) with column rescaling to one, and rescale
      the matching stressor entries. Wiebe et al. 2018 §3.3 is the recipe. Needs a
      deployment curve (S-curve) over the remaining years.
- [ ] **Grid tape design (Delta) with the engine in the room.** The current "enabler"
      hypothesis is not a finished design. What EXIOBASE can express: lower losses as a
      coefficient change on the transmission and distribution service sectors' own
      electricity inputs; interconnectors as inter-regional electricity trade coefficients.
      Curtailment is not in the table, so storage/curtailment stories need another lever,
      possibly a ceiling lift on other tapes at the game layer. Schedule a dedicated
      design conversation; the fictional history stays on the game side.
- [ ] **Region 3 consumption footprint.** The game's ~7 Gt CO₂e/yr is built up from an EU
      anchor. First number the engine should return; every REDUCE sizing hangs off it.
      *2011 table, 2026-09-17:* 9.2 Gt CO₂e/yr consumption-based, with Russia and Turkey
      inside the region (world 44.5 Gt). The 2050 figure waits on the baseline.
- [ ] **Per-region brick calibration** (one 10-reactor block's abatement on that region's
      grid), and later a global-grid-average anchor.
- [ ] **Rebalancing weighting scheme.** Flat proportional (placeholder) vs income
      elasticity (Bjelle et al. 2021, Cap et al. Eq. 1) vs sufficiency-targeted. One
      function, one weighting argument. Rung 2 (elasticity) is cheap and probably
      low-yield for Europe; do it to retire the arbitrary assumption. Applies to SWAP and
      to BUILD reallocation; REDUCE does not rebalance (decided above).
- [ ] **`eca_buy_less` basket.** Recommended Basket A (goods and leisure, protected list:
      housing, food, household energy, vehicle fuel). Decide whether government and NPISH
      demand are spared.
- [ ] **Lifetime extension apportionment `k`** per durable product group: split the effect
      between a volume fall in `y` and an intensity fall in `S`. Never both.
- [ ] **Tape sizing figures — firm up the external numbers.** Three numbers in
      `data/tech_choices/options.toml` come from outside the IO table and convert a tape's
      real-world cover into a fraction of a product basket. They are sourced and stated,
      but they are order-of-magnitude and each is the largest single uncertainty in its
      tape's `max_reducible_fraction`:
      - **Commuting's share of household car distance, ~30%** (Eurostat passenger mobility
        gives 27% in Germany to 47% in Croatia, of *daily* distance). Wanted: a share of
        *annual* vehicle-km, for Region 3 rather than the EU, and ideally by fuel spend
        rather than distance, since EXIOBASE's basket is money.
      - **Teleworkable share of the Region 3 workforce, ~35%** (Dingel & Neiman 2020 and
        Sostero et al. 2020 both give 37% for the US and the EU; shaded down for the
        region's middle-income economies). Wanted: the non-EU parts of Region 3 sized
        properly rather than by judgement.
      - **Do teleworkable workers commute by car at the regional average?** Assumed yes.
        Unlikely to be exactly true in either direction — office work is more urban, where
        car mode share is lower, but office commutes are longer. A mode-share-by-occupation
        source would settle it.
      Only `eca_remote_work_commuters` depends on these today. `eca_buy_less` and
      `eca_extended_product_lifetimes` derive their fractions from their own stated
      ceilings and need no external figure. Full citations in `docs/references.md`.
- [ ] **The 2011 → 2026 → 2050 walk, replacing the intensity scalars.** Split into its two
      stages 2026-09-21; `engine/intensity.py` now holds one factor for each, composing by
      multiplication. Both are stand-ins for walking the table forward, but they are at very
      different stages of being defensible and should be retired separately:
      - **2011 → 2026, currently 0.73. OBSERVED, and sourced** to the ~2.1%/yr fall in the
        carbon intensity of world output (Enerdata; 27% below 2010 by 2025, the same fifteen
        year span, so the published figure carries over directly). Good enough to
        ship. The improvement available is to stop using one economy-wide factor and correct
        the actual rows — the 2011 table predates the collapse in solar and wind cost and most
        of European coal retirement, so its *electricity* rows are much further out than its
        average. Per-sector correction against IEA *Electricity* / EEA series would be a
        genuine gain and needs no scenario agreement.
      - **2026 → 2050, currently 0.60. SCENARIO**, and simply the observed rate run on.
        Replace with a real SSP2 run — `jobs/apply_growth.py`, sequencing item 5b. This is the
        half nobody can check and the one to do properly first.
      *Worth recording, because the split surfaced it:* the single 0.6 these replaced implied
      the observed 0.73 followed by 0.82 — decarbonisation slowing to ~0.8%/yr after 2026,
      about a third of the rate actually being managed before it. Nobody had argued for that;
      it was an artefact of picking one round number. Composed honestly the correction is
      ~0.44, so **every headline figure is ~27% smaller than under 0.6.**
      *Done when:* `intensity_scalar` reads from a walked baseline rather than constants, and
      the constants are deleted rather than left beside it.
- [x] ~~**Weighted baskets.**~~ Done 2026-09-21. `scale_final_demand_per_product` is the
      general form and the flat one delegates to it; `apply_reduce` gained `weights` and
      `direct_emissions_driver`. The lifetimes tape runs on eight products at `N/(life+N)`
      with N = 4, and remote work widened to four products with Motor Gasoline driving `F_Y`.
      Linearity in the headline fraction holds with uneven weights and is tested.
- [ ] **Replace the provisional direct-household (`F_Y`) shares with fuel-resolved emissions.** The characterised impacts
      account is resolved by region and final-demand category, not by purchased product.
      The MVP now scales only a named share: road transport uses the 32.9% share of Region 3
      household `Energy Carrier Net Total` reported as `TROA`; gas uses 27.4%, inferred from
      the tape's gross heating anchor against total direct GHG. This removes the known whole-
      column overstatement, but energy share is not emissions share and the gas figure is an
      external-anchor proxy. Derive gas, petrol and diesel GHG shares from a regional energy
      balance and carrier-specific combustion factors, then promote the affected records
      from provisional if the result is stable.
- [ ] **Mean product lifetimes, against Vita et al. 2019.** The weights in
      `appliances_and_devices` are `N / (mean life + N)`, and the mean lives behind them
      (~4 yr devices and clothing, ~7 medical/precision, ~11 white goods, ~12 furniture) are
      order-of-magnitude figures, not sourced. They are the largest uncertainty in the tape
      and it is now the second-largest REDUCE tape, so they matter more than they did. Vita
      et al. 2019 is already in `docs/references.md`.
- [ ] **Is four extra years the right lifetimes ceiling?** The ceiling is expressed in years
      rather than as a demand fraction, which is right — the fraction differs per product. But
      N = 4 is a judgement about where repair stops paying, not a measurement, and it sets the
      tape's whole magnitude. The cover (+1 year) and the ceiling (+4) are also related
      non-linearly, so the linear deployment curve understates partial rollouts slightly; the
      endpoints are exact.
- [ ] **Remote work's cover needs re-sizing, or its ceiling re-checking.** The engine says 3
      copies where the game sized ~9. The difference is the teleworkable share: a sourced
      ~35% of workers times commuting's ~30% of household car distance gives an 11% ceiling
      on the basket, where the earlier working figure was 28%. Either the cover moves (the
      normal handshake) or the commuting-share figure is wrong — see the tape sizing figures
      item above, which is the same uncertainty seen from the other end.
- [ ] **Region 3 population and workforce.** Several ceilings scale per head (nuclear off
      France's build rate, remote work off the teleworkable share) and both figures are
      currently order-of-magnitude guesses: ~900 M people, ~300-400 M workers. Derive them
      from the region concordance's country list against a public population series, and
      record them once where the ceilings can cite them.
- [ ] **Nuclear ceiling: forging capacity, not population.** The France-scaled ceiling
      (~650 reactors over a ten-year mobilisation, ~19 kWh/d/person) scales a build rate by
      population, which ignores the constraint the literature actually names: heavy forging
      capacity for reactor pressure vessels is concentrated in a handful of plants worldwide.
      Population scaling is fine while the tape is effectively ungated at cohort size, but if
      the ceiling ever needs to bind, forging is where to look. See
      `docs/design/tape_records.md` §3.
- [ ] **Basic → purchaser prices from the real matrices.** `engine/prices.py` uses a universal
      1.20 markup where EXIOBASE carries TT (taxes and subsidies on products) and TTM (trade
      and transport margins) sector by sector. Energy products are taxed far more heavily than
      1.20 and services far less, so a fuel tape's spend figure is the least reliable monetary
      number the engine produces. See `docs/design/units_and_currency.md` §2.
- [ ] **Size covers on the real deployment curve, not the flat one.** Covers are sized on
      `cumulative_full_flat` but scored on the curves the game draws, and the gap is not
      wing-neutral: a REDUCE tape delivers 0.91 of its flat figure, a 10-year BUILD 0.77, a
      20-year BUILD 0.57. **A BUILD tape therefore delivers ~16% less than a REDUCE tape sized
      to the same flat brick**, before construction emissions add another 2–3%. That is a
      systematic bias that makes building look better on paper than it plays, and its danger
      is invisibility: if it surfaces in playtesting as "BUILD feels weak", the tempting fix
      is a thumb on a ceiling, which would treat a sizing artefact as a physical finding.
      Keep the flat figure as a wing-neutral comparison and label it as that.
      *Done when:* the export carries a curve-corrected cumulative alongside the flat one.
- [ ] **Decide whether the brick is CO₂ or CO₂e.** The anchor is denominated in CO₂e; the
      game's temperature reading uses TCRE, which is defined on CO₂ alone. Measured per tape,
      CO₂ is 88.0% of CO₂e for remote work, 80.8% for buy-less and 79.6% for lifetimes — so
      **two tapes worth the same CO₂e brick differ by about a tenth in their effect on 2100
      temperature.** A fuel tape is nearly pure CO₂; a manufactured-goods tape carries more
      methane and nitrous oxide from its supply chains. Carrying both figures is already
      decided, so the data will be there; what is missing is a statement of which one the
      anchor *is*. Either is defensible — a warming anchor is more honest about what the game
      measures, a CO₂e anchor is more honest about what a tape removes.
- [ ] **Separate the brick reading from `copies`.** Both are currently "cumulative at full
      ceiling ÷ 1 Gt", which makes them the same number computed twice while the cover's own
      value never appears. The intent is that the *cover* is sized to one brick and `copies`
      is how many covers fit inside the ceiling. Linearity means one solve yields both, so
      this is a definitional fix, not extra computation — but until it is written down,
      "the brick reading" means two things depending on who is reading.
- [ ] **Check world vs regional deltas when T6 lands.** Deltas are world totals. For a
      consumption-based REDUCE tape on Region 3 the two coincide almost exactly. For a BUILD
      tape that changes Region 3's electricity recipe they may not, because output shifts
      across borders — worth measuring rather than assuming the REDUCE result carries over.
- [ ] **Tape interactions — start with the ones that share a constraint.** Ceilings are
      currently stated independently and are not all additive: nuclear and fusion compete for
      the same heavy forging capacity, and electrifying cars and banning gas boilers land
      their new demand on the same grid. A stack that adds every ceiling is an upper bound on
      an upper bound.
      This may be cheaper to model than it looks. The full version — re-solving a world with
      several shocks applied together — is the queue/worker design and is far off. But the
      **pairwise** version is close: a table of `(tape A played) → (tape B's ceiling or delta
      reduced by X)`, applied by whoever assembles the score. Most pairs are independent and
      need no entry; the interesting ones are few and nameable.
      *Worth deciding first:* whether an interaction reduces the other tape's **ceiling** (you
      cannot build both) or its **delta** (you can, but the second one abates less because the
      first already cleaned the grid). Those are different claims and probably both occur —
      forging capacity is the first kind, a decarbonised grid the second.
      *Start by writing the assumption down*, even with no numbers: which pairs interact, in
      which direction, and roughly how strongly. That is useful before it is implemented, and
      it is what stops the export's independence being mistaken for a finding.
- [ ] **Multiple simultaneous tapes.** MVP scores one tape vs baseline. When does the
      engine score against baseline plus the day's other tapes?
- [ ] **Net-zero threshold and scope** if the game ever displays "reached net zero":
      regional or global, and how close counts.

---

## Parked ideas

- Community-authored scenario library living in this repo, with the game curating which
  scenario runs per region and day (game architecture fork F5, unsettled).
- Companion regions doc with the full EXIOBASE code table and cross-model mapping notes
  (IPCC, World Bank, IMAGE/REMIND). Requested by the game's REGIONS doc.
