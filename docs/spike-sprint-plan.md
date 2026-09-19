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
2. [ ] **T2 — tape records and concordance, REDUCE rows first.**
       `data/tech_choices/options.toml` and `data/concordances/exiobase_to_scenario.csv`.
       Populate all nine records' *fields* but only the three REDUCE baskets need to be
       complete for sprint 2. Baskets use exact `products.txt` labels; the loader validates
       every product against the aggregated table's index. Each record carries
       `regional_ceiling` with its basis stated.
3. [ ] **T3 — the three REDUCE tapes through the existing path.** `apply_reduce` already
       works; this is baskets plus the `F_Y` fix below.
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
the stubs that have none (backlog item 10) so the TODOs stop pointing at a file.

---

## Sprint 3 — the other two wings

T4 (consumer-side SWAP), T5 (BUILD construction phase), T6 (BUILD operating phase, the
A-matrix mix change), T8 (fusion as nuclear with different build years and capex). Then T9
in full and T10's docs. T7 (grid) stays held until the game settles the tape's mechanism —
see Decisions below.

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
