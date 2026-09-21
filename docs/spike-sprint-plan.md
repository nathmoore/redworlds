# Sprint plan — the next few steps out of backlog.md, and why in this order

The principle: get one number out of the real model as early as possible, on the cheapest
path, and only then build the expensive parts. Each step is one function, one test file,
sized for a single session with the backlog entry as its brief.

---

## Sprint 1 — done 2026-09-17/18

Steps 1–4 and 5a landed in five commits on `main` (not pushed). 62 tests pass, 11 skipped.

1. [x] **`load_config`** (issue #5). Unblocked the integration fixture, so everything
       downstream is checked against real EXIOBASE rather than only the test world.
2. [x] **`scale_final_demand` and `get_sector_emissions`.** Plus `get_region_emissions` and
       `recalculate_from_final_demand` on the cheap Y-side path that reuses the Leontief
       inverse. Two pymrio traps found and handled: the coefficient reset also drops `Y`,
       and the plain reset leaves stale extension accounts. All emissions reads are
       consumption-based (`D_cba`).
3. [x] **`apply_reduce`** (issue #8). Households, NPISH and government only, never GFCF;
       re-spends nothing; negative cuts accepted as the game's backfire.
4. [x] **`annual_delta`, `cumulative_delta`, `gdp_impact`.** Convention set, worth
       knowing: **the delta carries the sign and the curve is a 0→1 deployed fraction**, so
       BUILD is two calls summed rather than one curve that flips sign.
5a. [x] **Capital endogenisation.** `load_capital_use` (Kbar `.mat`, ISO-3 region codes
       translated explicitly) and `endogenise_capital`. Three real-data integration tests
       pass. Taiwan settled as region 6.

**The first real number, on the 2011 table** (`examples/03_first_reduce_number.ipynb`):

| Quantity | Value |
|---|---|
| World consumption footprint | 44.5 Gt CO₂e/yr |
| Region 3 consumption footprint | 9.2 Gt CO₂e/yr |
| 1% cut in Region 3 household demand | −59 Mt CO₂e/yr |
| Cut equal to one brick, flat deployment | **~0.33%** |

Against the contract's 0.4–0.5% guess — slightly lower because 2011 intensities are dirtier
than 2050's will be. The two agree to well within the precision either deserves.

---

## Sprint 2 — get a real table into the game's hands, on three tapes

**The change of shape from the original plan.** The plan's own principle says get a number
out early on the cheapest path. Applied again with what sprint 1 learned, it says something
the first draft did not: **do not wait for all three wings before exporting.** The game's
consumer (`tape_table_<date>.json`) does not care which wings are present — the PHP side
looks tapes up by id. So a table containing only the three REDUCE tapes, on the 2011 basis,
is enough to unblock the game's entire server and client path (its backlog 6 §B.2–B.4, §C.3),
which is otherwise fully blocked on this repo.

That is worth more than a complete table a fortnight later, because it converts the game's
remaining work from *blocked* to *in progress*, and every later export is a re-run of a job
that is required to be byte-identically regenerable anyway.

The SSP2 walk moves **after** this, not before. It is the judgement-heavy step, it now has
the REDUCE numbers it wanted first, and nothing about the table's shape depends on it — only
the magnitudes, which are labelled provisional either way.

1. [x] **T1 — cache the aggregated baseline. Done 2026-09-19.** `just baseline` runs
       `jobs/build_baseline.py`: load 2011 pxp → `aggregate_regions` → `calc_all` →
       `endogenise_capital` → `calc_all` → persist to `data/worlds/baseline_2011_agg7/`.
       **Both done-conditions met:** the cached world reads **44.5 Gt CO₂e/yr**, matching
       notebook 03, and `pymrio.load_all` returns it in **6.1 s** (117 MB parquet) against a
       **4 min 10 s** build. The SSP2 walk is a TODO in the module docstring, as planned.

       *Aggregating before endogenising is what makes it four minutes rather than nineteen* —
       the Leontief inversion is then 1,400 × 1,400 rather than 9,800 × 9,800, and the answer
       is identical because both `A` and `K` are flows over output and flows aggregate
       linearly. It needed one new engine function, `aggregate_capital_use`, to group the
       Kbar the same way and reindex it onto the aggregated table's own index — grouping
       alone returns regions alphabetically while pymrio's `aggregate` keeps concordance
       order, which would misalign silently.

       The 44.5 Gt match is a real check rather than a tautology: endogenisation rewrites `A`
       and `Y` and re-solves the whole system, so a single mislabelled region would move it.

       Negative net-investment diagnostic run and recorded — see `backlog.md`. The short
       version: 90% of the −2.25 T EUR is genuine same-country disinvestment, not trade
       mismatch, concentrated in *Construction work (45)* and in the US, and it is 2011
       being a post-crisis construction trough rather than an artefact. The decision to keep
       the cells stands; the trough is worth an explicit decision at 5b and worth knowing
       about at T5.
2. [x] **T2 — tape records and concordance. Done 2026-09-19.** All nine records in
       `options.toml`, eight named baskets in `exiobase_to_scenario.csv`, and
       `jobs/tape_records.py` to load and check them. Three REDUCE records are `ready`; the
       other six carry their fields and are `pending`, so the export schema is right first
       time. Every ceiling states its basis.

       Records name a `scenario_category` and the concordance says what is in it, so two
       tapes can share a basket and every product label sits in one file. `validate_baskets`
       checks them against the table the tapes will actually run on, because a label is only
       right or wrong relative to a particular table — and a mistyped one is invisible:
       pandas selects nothing and the tape ships a plausible zero.

       **The cross-check worth knowing about:** the contract estimated basket A at "~1.4% of
       the basket per brick" from literature. The table says **1.34%**. Two independent
       routes, same number.

3. [x] **T3 — the three REDUCE tapes through the existing path. Done 2026-09-20,
       re-solved 2026-09-21 after weighted baskets.** `jobs/run_tapes.py` turns a record into
       an engine call and returns the tape's numbers.

       **Linearity is asserted, not assumed.** The precomputed-table design (contract §4.4)
       rests on solving each tape once at full deployment and letting the game multiply by
       the outcome fraction. Tests pin it to 1e-9 — with the `F_Y` correction, and with
       uneven weights. If it were only approximately true, every score the game computes
       would be wrong by an amount nobody could see.

3a. [x] **Weighted baskets, and the record realignment. Done 2026-09-21.** A basket can now
       be cut unevenly: `scale_final_demand_per_product` is the general form (the flat one
       delegates to it), and `apply_reduce` gained `weights` plus `direct_emissions_driver`.
       The driver is what makes the wider baskets possible — with uneven weights "the
       basket's change" is several numbers, so the fuel burnt at home has to name the row it
       follows rather than ride an average that describes nothing.

       Records realigned against the game's tape modelling sheet, which an earlier pass had
       not read. Buy-less to households only; lifetimes to eight products at
       `N / (life + N)` with N = 4; remote work widened to four products with Motor Gasoline
       driving `F_Y`; **fusion and smart grid stripped of ceilings** — fusion because its
       uncertainty belongs in the outcome band, smart grid because its mechanism is
       undecided; nuclear raised from 400 TWh/yr to 650 reactors on the France anchor.

       **Re-solved, 2011 basis and 2050 basis:**

       | Tape | Products | 2011 Gt | 2050 Gt | Copies |
       |---|---|---|---|---|
       | `eca_buy_less` | 13 | −18.6 | **−8.2** | 8 |
       | `eca_extended_product_lifetimes` | 8 | −12.2 | **−5.3** | 5 |
       | `eca_remote_work_commuters` | 4 | −8.1 | **−3.6** | 3 |

       Lifetimes moved most — nearly four times its old figure — because it gained clothing
       and furniture and a ceiling expressed in years rather than a flat 50%. The spread of
       copies tightened from 19/3/7 to 8/5/3, which is a far more playable shelf and was not
       aimed at: it fell out of using the sheet's mechanisms.

       Against the game's own expectations (~10 / 3–5 / ~9) buy-less and lifetimes land, and
       **remote work comes in at 3 against ~9**. That is the engine reporting and the cover
       needing to move, which is the handshake working. It follows from a sourced 0.11
       ceiling where the earlier guess was 0.28.
4. [ ] **T9-partial — the export job, three tapes.** `jobs/export_tape_table.py` writing
       `data/exports/tape_table_<date>.json` with the full per-tape schema and file-level
       `baseline`, `intensity_scalar_2050`, `units`. Records for the six unbuilt tapes are
       either absent or present with a `status: "pending"` field — **decide which, because
       the game has to handle it either way and absent is probably kinder.** A JSON schema
       beside it; `just export-tapes` regenerates byte-identically.
5. [ ] **5b — `build_baseline` composition and the SSP2 2011 → 2050 walk.** The
       judgement-heavy step, now with real REDUCE numbers to sanity-check against. Re-run
       T9 afterwards; the game gets a second table and changes no code.

**Also in this sprint, cheap and unblocking:** `gh auth login`, then create the issues for
the stubs that have none (backlog item 10) so the TODOs stop pointing at a file. Still to do
— `gh auth login` is interactive and has not been run.

**Two corrections to this plan, found while building it.** Decision 2 below says the gas
tape's `F_Y` fix bites at T3. It does not: the contract's tape table has
`eca_ban_gas_supply` as a SWAP, so it bites at T4 in sprint 3. The fix itself is built and
wired into `apply_reduce`; `apply_swap` will need the same wiring. And the three REDUCE
tapes are therefore `eca_buy_less`, `eca_extended_product_lifetimes` and
`eca_remote_work_commuters`.

---

## Sprint 3 — the other two wings

**What sprint 2 changed about this sprint.** Four things carry over and are worth holding
before picking up a task, because each one either makes a step cheaper or makes a step
riskier than the original plan assumed.

1. **BUILD breaks the linearity everything else relies on.** Y-side shocks are exactly linear
   in the deployed fraction, which is why one solve per tape serves every outcome fraction —
   asserted to 1e-9 in sprint 2. An A-matrix change is not linear: re-inverting `L` after a
   coefficient shift does not scale. So BUILD tapes need solving at 0.25 / 0.5 / 0.75 / 1.0
   and interpolating, the export schema has to carry all four, and **the linearity test must
   not be copied across to BUILD** — it would pass at the endpoints and lie in between.
2. **The flat-curve sizing bias bites BUILD hardest** (`tape_records.md` §10.2). A 10-year
   BUILD delivers 0.765 of its flat figure against REDUCE's 0.912. Produce curve-corrected
   cumulatives from the start rather than retrofitting them, or T5/T6 will look ~16% better
   than they play and the error will be invisible until playtesting misattributes it.
3. **Weighted baskets exist**, so SWAP can move products at their own rates without the
   workarounds sprint 2 needed, and `apply_swap` must gain the `F_Y` correction that
   `apply_reduce` has — the gas tape burns fuel at home and is a SWAP.
4. **The ceiling method is settled** — a rate times a mobilisation window, per-person units,
   economics and acceptability left out (`tape_records.md` §4–6). T5 and T8 can use it
   directly. Fusion needs no ceiling at all, which removes a step.

**Order, and why.** SWAP before BUILD: `apply_swap` is two `scale_final_demand` calls plus a
flat re-spend, so it lands on machinery that already exists, and it gets a second wing into
the export weeks before the A-matrix work is finished.

- [ ] **T4 — consumer-side SWAP** (`eca_electric_vehicle_transition`, `eca_ban_gas_supply`).
      Cut product A in the region's household column, add product B at the tape's
      service-equivalent (COP 3 for gas → heat-pump electricity, ~⅓ energy for petrol → EV
      electricity), priced; re-spend the remainder flat across the household basket. Both
      tapes need `F_Y` wired through `apply_swap`. *Done when:* `gdp_impact` ≈ 0 — the
      closed-budget check, and the cleanest possible test that a SWAP preserves money.
- [ ] **T5 — BUILD, construction phase.** GFCF injection across *Construction work (45)* 40%,
      *Machinery and equipment n.e.c. (29)* 42%, *Electrical machinery (31)* 9%, *Other
      business services (74)* 9%, spread over `build_years`. Returns a *positive* annual
      delta. Still Y-side, so still linear. *Done when:* nuclear's construction total is a
      few percent of its operating abatement — and note it lands on a 2011 construction
      trough, which is deliberate and recorded, not a bug.
- [ ] **T6 — BUILD, operating phase.** The A-matrix electricity-mix change, and the hardest
      step in the project so far. Re-inverting `L` per tape is minutes, not seconds, which is
      what makes the four-point deployment sampling a real cost rather than a detail.
      *Done when:* nuclear lands in the contract's 0.5–1.8 Gt range at the ten-reactor cover.
      *Check first:* pymrio issue #72 reports surprising GHG intensities for solar PV and
      geothermal in EXIOBASE 3 — verify both sectors' coefficients before trusting a result.
- [ ] **T8 — fusion.** Nuclear's mechanics at 20 build years and 2× capex per GW. Cheap once
      T5 and T6 exist, and it carries no ceiling, so it is mostly a record and a re-run.
- [ ] **T9 in full** — all nine tapes, with the BUILD deployment samples and both CO₂ and
      CO₂e per tape.
- [ ] **T10 — docs.** Fold sprint 3's assumptions into `assumptions.md`, and revisit
      `tape_records.md` §10 with BUILD numbers in hand: the flat-curve finding was derived
      from curve arithmetic alone and deserves confirming against a real BUILD solve.

**T7, the grid tape, stays held** — two candidate mechanisms need different shocks and the
game has not settled which. Building either first risks throwing the work away. It is stopped
at the mechanism gate rather than failing, which is that gate working.

---

## Decisions this needs, in the order they bite

1. [x] **BUILD capex: injection or reallocation — decided: injection.** The backlog carried
   this as open and *"Nathan's call, design-flavoured"*; it had already been decided on the
   game side and only needed propagating (confirmed 2026-09-18). The game's decision log (2026-09-18, the Beta Day entry) specifies the
   construction phase as a GFCF injection into construction / machinery / electrical
   machinery / other business services on the Wood–Wiebe SI1 split, with the operating phase
   as a separate A-matrix change. Backlog item closed; the reallocation flag stays exposed
   but off, so the cross-check stays cheap. *Bites at T5, sprint 3.*
2. [x] **Direct household emissions under a REDUCE (`F_Y`) — decided 2026-09-18: fix it in
   T3.** The backlog said *"fix when the first such tape is sized"*. That time is now: **two Beta Day tapes are exactly
   this case** — the remote-work tape cuts vehicle fuel, and the gas tape cuts household gas.
   Both are wrong under the current normalisation, and `F_Y` is 11% of the world total
   (5.1 of 44.5 Gt CO₂e), not a rounding error. Scale the `F_Y` column by the fuel product's
   own change. *Bites at T3.*
3. [x] **Negative net-investment cells — decided 2026-09-18: keep them.** −2.25 T EUR across
   6,363 cells. Södersten et al. treat net investment as a residual and the accounting identity
   holds, so leave it as it falls. Still run the diagnostic inside T1 and record it — how much
   is supplier-region trade mismatch versus genuine same-region disinvestment — and revisit only
   if it is mostly the latter. *Bites at T1, cosmetically.*
4. [x] **CO₂ versus CO₂e in the export — decided 2026-09-18: carry both.** Checked against
   the real tables rather than from memory, because the concern raised was that CO₂e might be
   less complete in EXIOBASE. It is not, and the fix is nearly free: **both quantities already
   exist as pre-characterised rows in the `impacts` extension**, so this is one extra row read,
   not a new calculation. Full row names, the reconciliation and the two traps are in
   `backlog.md` §Emissions accounting. The headline:

   | | World 2011, F + F_Y | Unit |
   |---|---|---|
   | All-GHG (what we read now) | 44.5 Gt CO₂e — matches notebook 03 | kg CO₂ eq. |
   | CO₂ only | 32.5 Gt CO₂ — real-world fossil+cement ~34 | **Gg** |

   ⚠ **The units differ by 10⁶.** Adding the CO₂ field by copying the GHG read path gives an
   answer a million times out. Read `impacts/unit.txt` per row.

   ⚠ **Never sum rows to build a total.** `impacts` holds the same emissions several times —
   `Carbon dioxide (CO2) CO2EQ ...` duplicates `Carbon dioxide (CO2) ...`, the two
   fuel-combustion rows are nested subsets of it, and there are six GWP variants of the GHG
   total. The existing code is already right about this (it reads one characterised row); the
   point is to keep it that way. *Bites at T9.*

5. **T7, the grid tape.** Still correctly held: two candidate mechanisms needing different
   shocks, and the game side has an open design conversation. Nothing to do here until that
   lands. *Bites at sprint 3, or not at all this epic.*
6. **`regional_ceiling` per tape** (T2). The game wants these for a proposed "tapes in
   stock" mechanic that is still tentative on its side. Record the ceiling and its basis
   regardless — it is a defensible engine fact either way — but do not let the game's
   undecided mechanic hold up T2.

---

## What the game is waiting on, precisely

Its backlog 6 §B.2 (the deployment curve ported to PHP), §B.3 (the commit endpoint), §D
(calibration) and §C.3 (the board UI) all consume `data/exports/tape_table_<date>.json`.
Everything else on that side is built: the resolver is ported and parity-checked against the
JS, the leaderboard store and its endpoint are done. **One partial export unblocks all of it.**

*Citations to the game's decision log above are provenance, not links — that repo is private.*
