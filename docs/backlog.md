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
2. [ ] `load_config()` — GitHub issue #5.
3. [ ] `scale_final_demand()` and `get_sector_emissions()` — issues #11, #13. First REDUCE
       runs end to end on `pymrio.load_test()`.
4. [x] ~~A test-world concordance fixture under `tests/fixtures/` so region aggregation gets
       real unit tests.~~ Done 2026-09-16 (`tests/fixtures/test_world_regions.csv`; the
       `exiobase_mrio` integration fixture also exists now). Scenario-mapping fixture still to do.
5. [ ] Validate `region_mapping.csv` against the real EXIOBASE 3.8.2 download (integration
       test); settle Taiwan (CSV says region 7, game design says 6).
6. [ ] `jobs/build_baseline.py` stub: 2011 EXIOBASE → capital endogenised → SSP2 2050
       world → 2050–2100 trajectory. First check the capital-flow data resolution (see
       Modelling decisions).
7. [ ] `score_tape()` composition returning the result shape in the contract doc §4.3.
8. [ ] First empirical notebook: "what does a 0.5% cut in Region 3 household demand do to
       cumulative CO2 2050–2100?" This is the moment outsiders can use the repo.
9. [x] ~~Fix stub TODO issue numbers (issue #10) and merge the two references files.~~ Done
       2026-09-16 for the five issues that exist (#5–#9). The engine primitives, `capital.py`,
       `scoring.py` and `build_baseline.py` have no issues yet (issue #10 assumed #11–#15,
       which Dependabot took): their TODOs point here.
10. [ ] Create GitHub issues for the stubs without one (`scale_final_demand`,
       `shift_sector_share`, `get_sector_emissions`, `rebalance_economy`, `generate_scenario`,
       `load_capital_use`, `endogenise_capital`, `annual_delta`, `cumulative_delta`,
       `build_baseline`), update their TODO lines, close #10. Needs `gh auth login`.

Phase 2, not on the MVP path: per-player worlds, the shared job queue, multi-tape
interaction, nightly growth.

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

### Open

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
      displacement, consistent with the baseline's treatment of every other plant; net it
      out of the injection later if it matters). The REDUCE "non-capital Y" basket excludes
      only the remaining net-investment column. *Checks before building:*
      - [x] ~~Confirm the published capital-flow matrices exist at this repo's resolution.~~
            Confirmed 2026-09-16: Zenodo record 7073276 (Wood & Södersten) has pxp and ixi
            files for 1995–2020, CC-BY-4.0; the file is `Kbar_exio_v3_8_2_2011_cfc_pxp.mat`
            (flow form, MEUR; coefficient form is Kbar · x̂⁻¹). Reading `.mat` needs scipy
            (add as a dependency when implementing `load_capital_use`).
      - [ ] Carry the capital coefficients through the 2011 → 2050 extrapolation
            consistently.
- [ ] **BUILD capex (b): where does the money come from?** Injection (new money, GDP
      rises, strongest J-curve, matches BU1 and Wiebe) vs reallocation within the
      remaining GFCF column (GDP-neutral, crowds out other investment, slightly softens
      the hump, matches the game's latest "BUILD GDP-neutral reallocation" framing). Both
      are one flag on `rebalance_economy`. **Nathan's call, design-flavoured.** MVP can
      ship injection and expose the flag.
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
