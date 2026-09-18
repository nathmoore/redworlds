# What Red Carbon needs from Red Worlds

**Status:** harvest, 2026-09-16. This doc collects every decision made in the Red Carbon
game design between March and September 2026 that binds this engine, plus the modelling
questions the game has parked "for Red Worlds". The game owns *why* and the numbers it
needs; this repo owns *how the IO maths produces them*.

> **Reading the citations.** References like "game `DECISIONS.md` 2026-06-25" point into the
> game's private design log. They are provenance for the maintainer, not links you can
> follow. Everything you need to build against is stated here in full.

Where this doc and the older design docs in this folder disagree, **this doc wins** — the
older docs describe the March 2026 game and are listed as stale in §8. Game design thinking
(characters, story, balance philosophy) stays in the game repo and is deliberately not
copied here.

---

## 1. The time window and the score

- **In-game "now" is 2050.** The 1.5°C and 2°C budgets have expired; the game opens at a
  3.2°C-in-2100 reading. (Game repo: `DECISIONS.md` 2026-04-30; `TECHNICAL_IMPLEMENTATION.md`.)
- **The score is cumulative CO₂ abated 2050–2100**, one point per tonne, for a single
  intervention ("tape") scored against a do-nothing baseline. Civic effects reach the score
  only by changing the carbon (a delayed build, a rebound, non-adoption), never as a
  multiplier. (`DECISIONS.md` 2026-06-25.)
- **Temperature is derived, not modelled:** `ΔT ≈ 0.45 °C per 1000 Gt CO₂` (TCRE, Allen et
  al. 2022). The game displays "homes saved" as a monotonic lookup from cumulative CO₂. Red
  Worlds returns tonnes; the game does the rest.
- **Every tape covers the full 50-year window.** BUILD tapes carry a J-curve: construction
  emissions in years 1–N (there is no budget headroom to absorb them), then clean output in
  years N+1–50. No stacking time blocks per day.

**What this replaces in this repo:** the "Baseline year 2027, advance one simulation year
per night" model in `assumptions.md` and `architecture.md`. The nightly `apply_growth` job
still has a role (building the 2050 baseline and the 2050→2100 trajectory), but it is a
one-off baseline-construction step, not a per-player nightly tick. See §7.

---

## 2. The brick: gold-standard normalisation

The game collapsed "how much of the intervention" into the tape itself. **Every tape is
pre-sized to deliver the same expected abatement at a reference play**, so the player's
choice between tapes is a real choice and no wing is a trap. The common currency is
cumulative tCO₂e 2050–2100, pegged to **one 10-reactor nuclear build block ≈ 1 Gt CO₂
cumulative** (plausible range 0.5–1.8 Gt; the displacement assumption of ~300 g/kWh
marginal grid intensity in a 2050 ECA grid does almost all the work). (`DECISIONS.md`
2026-06-24, 2026-07-10, 2026-08-06.)

Consequences for the engine:

- **Deployment magnitudes are outputs, not inputs.** "How many cars / GW / homes equals one
  brick" is a question Red Worlds answers; the game's current cover numbers are
  one-significant-figure smell tests waiting to be superseded.
- **Per-region calibration.** One brick displaces more on a dirty grid than a clean one, so
  the peg is set per game region against that region's nuclear anchor. A cross-region
  global-grid-average anchor is a later refinement once the engine can compute it.
- **Tape availability is a curation-layer filter**, not an in-play dial: physical ceilings
  (MacKay-style land, resource, behavioural limits) decide which tapes a region offers and
  how many copies exist. Red Worlds should be able to report a tape's regional ceiling so
  the game can cap the count.
- **Aggregation guardrail.** Many players each playing one brick cannot be naively additive
  across cohorts (50 vs 5000 players). Collective scoring will sample or weight; the engine
  scores one tape at a time and does not need to solve this.

Working brick-equivalents from the game's 2026-08-06 sizing pass (authoring anchors only,
Region 3):

| Tape id | Wing | Cover magnitude sized to ~1 brick |
|---|---|---|
| `eca_nuclear` | BUILD | 10 reactors × 1.2 GW, CF ~90% → ~95 TWh/yr (the peg) |
| `eca_geothermal` | BUILD | ~13 GW at CF ~80% |
| `eca_electric_vehicle_transition` | SWAP | ~11 M cars at ~2 t/yr each |
| `eca_smart_grid` | SWAP | numberless (enabling, not emitting) |
| `eca_extended_product_lifetimes` | REDUCE | every appliance *and device* +1 year of life |
| `eca_buy_less` | REDUCE | ~0.5% of consumption across the region (basket undefined, see §5) |
| `eca_remote_work_commuters` | REDUCE | one commute day/week × ~100 M people |
| `eca_ban_gas_supply` | SWAP | ~12 M gas-heated homes |
| `eca_fusion` | BUILD | numberless (moonshot) |

---

## 3. Per-wing rebound and GDP treatment

Settled in the old `redcarbon-wp` architecture doc (assumptions BU1 / SW3 / RE2) and
restated in the game's `TECHNICAL_IMPLEMENTATION.md`. These are the rules
`engine/balancing.py` must implement:

| Wing | Rule | Money | Carbon credit |
|---|---|---|---|
| **BUILD (BU1)** | Construction capex is a **GFCF injection** spread across the build years; after completion, the electricity sector's emission intensity falls (phase 2). | Injection (or reallocation from other capital sectors — wording gap, see §6) | Construction emissions are real and front-loaded (the J-curve). |
| **SWAP (SW3)** | **Closed-system household budget rebalance**: the fossil saving is re-spent on electricity and the rest of the consumption basket. | Total preserved | The re-spend **is** the rebound; a SWAP's benefit is partly eroded by design. |
| **REDUCE (RE2)** | **Reduced spend exits the model — no rebalancing.** | Total falls (booked as a GDP reduction; the model returns `gdp_impact`) | Full credit, no rebound haircut. |

This matches the existing `assumptions.md` three-way split. Two additions from the game's
research since then:

- **Rebalancing and rebound are one function with a weighting argument.** SWAP/BUILD
  preserve the total, REDUCE does not; whatever weighting `rebalance_economy` uses for
  "where does freed money go" also gives the REDUCE-side rebound for free if a designer
  ever wants it. The v2 target is Cap et al. 2024 Eq. (1): scale each product's household
  demand by its income elasticity (Bjelle et al. 2021, 15 categories × 49 EXIOBASE
  regions), convert to budget shares, re-apply holding total household expenditure
  constant. Expect it to be low-yield for Europe (composition effects roughly cancel) but
  it retires an arbitrary flat-proportional assumption.
- **A cut's carbon depends on the mechanism that produced it.** The same money removed from
  Region 3's economy delivers roughly 1.6 bricks if households got poorer
  (elasticity-weighted: they protect heating, food, fuel) and ~2.9 if they chose to consume
  less (they cut flights and keep the heating). Recommended engine shape: the three
  weightings (flat / elasticity / sufficiency-targeted) are three arguments to the same
  rebalance call, and the game's push dial can degrade a REDUCE tape from the sufficiency
  weighting toward the contraction weighting as coercion rises.

---

## 4. The calling contract

### 4.1 Who calls whom

The only hard boundary in the whole system is this repo (runtime + CC BY-SA licence +
batch latency). The game resolves dice, variance and civic modifiers itself in a JS module
(`src/engine/finale-resolution/`) whose public surface is:

```
resolve({ tape_id, wing, push_level, civic_modifier_id })
  → { dice, outcome_band, outcome_fraction, civic_outcome, score, jcurve[{year, value}] }
```

Today `score` and `jcurve` are canned. **The planned wiring:** `resolve()` gains a thin
translation step that emits a Red Worlds `payload_json`, and the returned `result_json`
replaces the canned `score` and `jcurve`. Nothing else in the game changes. Transport is a
shared job-queue table (WordPress inserts a row; a Python worker claims it, writes
`progress_json` per step and `result_json` on completion; WordPress polls). That matches
the queue design already in `architecture.md`.

### 4.2 What the payload will carry

The game does **not** send `budget` / `build_years` / `pct_rollout` as free numbers the way
`game_mechanics.md` currently specifies. It sends a **tape id** plus the realised
**outcome fraction** of that tape's ceiling (0–1, occasionally negative for a REDUCE
backfire) and the **push level** (0.0–5.9). Everything physical about the tape lives in a
tape record. The game's tape-mining spike proposes each tape record carry a
`redworlds_contract` block; the fields it wants Red Worlds to define are:

| Field | Meaning | Example (`eca_nuclear`) |
|---|---|---|
| `action` | `build` / `swap` / `reduce` | `build` |
| `region_id` | game region 1–7 (not a label) | `3` |
| `scenario_category` | key into `exiobase_to_scenario.csv` | `electricity_generation` |
| `technology` / `from_technology`, `to_technology` / `sector` | keys into `options.toml` | `nuclear` |
| `matrix_target` | which matrix the shock hits: `Y`, `Z`, `A`, `GFCF`, `S` | `["GFCF_construction_phase", "A_post_build_energy_mix"]` |
| `budget_musd_2026_purchaser` | BUILD/SWAP cost in player-facing currency | `100000` |
| `build_years_reference` | reference build time; push and civic modifiers move it | `10` |
| `max_replaceable_fraction` / `max_reducible_fraction` | converts `outcome_fraction` to an engine `pct_rollout` / `pct_reduction` | — |
| `deployment_curve` | ramp shape over the 50 years (S-curve of diffusion) | — |

**Realised engine inputs** are therefore derived: `pct_reduction = outcome_fraction ×
max_reducible_fraction`, `pct_rollout = outcome_fraction × max_replaceable_fraction`,
`build_years = reference ± modifier time deltas`, `budget = reference × cost deltas`.

### 4.3 What the result must carry

From the game's `TECHNICAL_IMPLEMENTATION.md`, `MAINFRAME_PLAY_MODEL.md` §11 and the old
`redcarbon-wp` job schema:

```jsonc
{
  "co2_delta_cumulative_t": -1.02e9,        // signed; negative = abatement
  "jcurve": [{ "year": 2050, "value": ... }, ... { "year": 2100, "value": ... }],
                                             // annual delta vs baseline, 5-year blocks are enough
  "gdp_impact": ...,                         // REDUCE books a contraction; others ~0
  "baseline_cumulative_t": ...,              // do-nothing 2050–2100 for the region (or world)
  "emissions_unit": "kg CO2-eq",
  "progress": [ { "step": "load_baseline" }, { "step": "apply_shock" }, { "step": "solve" } ]
}
```

The game currently charts against a canned SSP2-shaped world baseline (~37 Gt/yr in 2050
falling to ~16 Gt/yr in 2100). It wants the real one back from here.

### 4.4 The Beta Day path: a precomputed table (decided 2026-09-18)

For the game's first scored playtest the queue in §4.1 is **not built**. Because the
payload varies only in `outcome_fraction` and `push_level`, and Y-side shocks are linear in
the fraction, each tape is solved **once, offline**, and the results ship to the game as a
JSON table. The game multiplies the tape's full-deployment annual deltas by the realised
fraction, runs the deployment curve (its own port of `engine/scoring.cumulative_delta`), and
computes the score server-side. Per-tape record:

```jsonc
{ "eca_nuclear": {
    "region_id": 3, "wing": "build",
    "annual_delta_construction": 1.2e10,   // kg CO2-eq per build year, full deployment
    "annual_delta_operating": -3.1e10,     // kg CO2-eq per operating year, full deployment
    "deltas_by_deployment": { "0.25": ..., "0.5": ..., "0.75": ... },  // BUILD only (A-matrix, non-linear)
    "gdp_impact_full": 0,
    "build_years_reference": 10,
    "deployment_curve": "build_default",
    "cover_magnitude": { "reactors": 10, "twh_per_year": 95 },
    "cumulative_full_flat": -1.02e12,
    "provenance": "jobs/export_tape_table.py @ <commit>" } }
```

File-level fields: `baseline` (which cached world), `intensity_scalar_2050` (one factor
applied by the game to every delta, standing in for the 2011 → 2050 intensity decline until
the SSP2 baseline exists), `units`. The queue/worker path stays the design for tapes that
must interact; the `result_json` it returns is the same shape the table carries per tape,
so the game's table code becomes the fallback rather than a rewrite.

Two modelling choices the game made for this path: BUILD's operating phase is an
**A-matrix electricity-mix change** (Wiebe et al. 2018 §3.3), not a demand-side product
substitution, because industrial electricity sits in `Z`; and SWAP is **consumer-side
only** with a flat re-spend. Both are recorded in `docs/backlog.md` §Beta Day tape table.

---

## 5. Per-tape modelling notes the game has already worked out

These are the engine-relevant conclusions from `docs/LitReview/claude-research/` and the
tape-mining spike in the game repo. Numbers are order-of-magnitude anchors.

- **Nuclear (BUILD).** 1 GW at CF 90% ≈ 7.9 TWh/yr; displaces ~3.2 Mt/yr vs gas at 400
  g/kWh, ~7 Mt/yr vs coal. Western build 10–15+ yrs from decision; China/Korea 5–8.
  Lifecycle intensity ~12 g/kWh, so construction debt is ~2–3% of gross and bites on
  *timing*, not lifetime sum. Capex breakdown by EXIOBASE industry for renewable
  technologies exists in Wood/Wiebe 2018 SI Table SI1 (e.g. nuclear 42% machinery, 40%
  construction, 9% electrical machinery, 9% other business) — a ready-made GFCF concordance
  for BUILD.
- **Geothermal (BUILD).** Proven-hotspot floor under an enhanced-geothermal ceiling; CF
  ~75–82%. Availability is hotspot-gated per region.
- **EVs (SWAP).** ~2–3 t/yr saved per car at ~12,000 km/yr; embodied payback ~1–2 yrs. Most
  exposed tape to the rebalancing upgrade: freed motoring money re-spends toward transport
  and recreation, including air travel.
- **Smart grid (SWAP, enabling).** Hypothesis: shocks to the technical coefficients of the
  electricity distribution sector (lower transmission losses ~6–8%, lower curtailment
  ~2–5%, demand response), plus inter-regional trade coefficients for interconnectors.
  **Open question: can distribution-sector coefficient shocks produce a standalone score
  competitive with direct tapes?** (`DECISIONS.md` 2026-03-26.)
- **Extended product lifetimes (REDUCE, RE2).** Fewer units made; the physical fact is
  invariant to vendor price response. Price compensation `k` apportions the change between
  a fall in `y` (volume, scales with `1−k`) and a fall in `S` for that product group
  (intensity, scales with `k`) — **apply one or the other, never both**, or the tonne is
  double-counted. Retooling is a small GFCF J-curve. Most abatement lands outside Region 3
  (appliances and electronics are imported); consumption-based accounting credits it
  correctly. White goods alone reach only ~0.14 brick; devices are the lever.
- **Buy less (REDUCE, RE2).** An across-the-board cut of non-capital final demand
  (households + NPISH + government; exclude GFCF so REDUCE never transacts in BUILD's
  currency) needs only **~0.4–0.5%** sustained for 50 years to equal one brick (range
  0.4–1.6% depending on intensity decline and rebound assumptions). Better: a **named
  basket** of EXIOBASE product groups with a protected list. Recommended Basket A = goods
  and leisure, excluding housing, food, household energy and vehicle fuel → ~1.4% of the
  basket per brick, progressive without means-testing. Basket product groups: apparel,
  textiles, leather, furniture, office machinery, radio/TV/comms equipment, electrical
  machinery, medical/precision instruments, motor vehicles, air transport, hotels and
  restaurants, recreation/culture/sport, tobacco. Employment: ~1.1 M in-region jobs per
  brick under static Leontief, or ~7 minutes off the working week if taken as hours.
- **Remote work (REDUCE).** ~0.13 t/yr per person per weekday avoided, net of home heating
  and non-drivers; rebound is the dominant uncertainty.
- **Cut gas (SWAP with REDUCE-like civic texture).** ~14,000 kWh/yr per gas-heated home ×
  0.203 kg/kWh = 2.8 t gross, ~1.9 t net of replacement electricity at COP ~3.

---

## 6. Contradictions and open modelling questions

The engine's real backlog is the set of modelling decisions the game could not make
without a working model. They are tracked as items in `docs/backlog.md` (§Modelling
decisions) so they can be worked, closed and promoted to GitHub issues. Headline ones:
the REDUCE rebound contradiction (factor of two), BUILD as injection vs reallocation, the
construction-emission multiplier, grid tapes as coefficient shocks, and which SSP builds
the 2050 baseline.

Method constraints to keep in view (Wiebe et al. 2018 §5, Vita et al. 2019): the MRIO is
purely demand-driven with GDP held constant across scenarios except where a wing rule says
otherwise; trade shares are constant; there is no price channel, so any price response is
an exogenous input; when a coefficient is changed its column must be rescaled to sum to
one; new technology must have been *produced* (model it as GFCF); stressors scale with
coefficients. Results are relative between scenarios, never absolute.

---

## 7. What the engine should look like given all this (recommendation)

The 2050 single-window model is simpler than the March 2026 design, and the simplification
is worth taking:

- **MVP is a stateless function**, `score_tape(baseline_2050, shock) → result_json`, run
  as a static comparative (one Leontief solve for the shocked world, annual delta vs
  baseline, multiplied through a deployment curve to give the 50-year cumulative and the
  J-curve). This is exactly Wiebe's "what if" method and it needs no per-player world, no
  nightly growth tick and no job queue to be *useful* — a notebook can call it.
- **The atomic units are shock primitives on a calculated IOSystem** (scale a final-demand
  slice; shift demand between two products; inject GFCF into construction sectors; rescale
  a column of `A` and the matching `S` entries; change electricity-mix coefficients).
  BUILD, SWAP and REDUCE are thin compositions of those. This is already the shape of
  `engine/io_tables.py` and issues #11–#15; keep it.
- **Per-player worlds, the queue and multi-tape interaction are phase 2**, unchanged in
  design from `architecture.md`, but not on the MVP path.
- **Time is a deployment curve, not a year-by-year simulation, until a year-by-year
  baseline exists.** The 2050→2100 baseline trajectory is a separate, cacheable artifact.

---

## 8. Red Worlds docs and data now stale (do not trust without checking here)

| File | What is stale |
|---|---|
| `docs/design/assumptions.md` | Baseline year 2027; nightly growth per player; "Decarbonator Deck" naming. Rebalancing split and price/currency sections are still right. |
| `docs/design/game_mechanics.md` | Payloads carry raw `budget`/`build_years`/`pct_rollout`; the game now sends tape id + outcome fraction (§4.2). "Regions rotate per simulation year" is gone. The region table puts Japan in region 6; the CSV (correctly, per the game) puts it in 7. |
| `docs/design/architecture.md` | Overnight-job flow and per-player world retention describe phase 2, not MVP. Queue contract itself still stands. |
| `examples/prompts/red_worlds_context.md` | Says baseline 2027. |
| `data/concordances/region_mapping.csv` vs game `REGIONS.md` | ~~Taiwan: CSV says region 7, game says region 6.~~ Settled 2026-09-17: region 6. Game doc also uses ISO-3 codes and lists many non-EXIOBASE countries that fall inside `WA`/`WL`/`WE`/`WF`/`WM` blocks. The game asked for a companion regions doc here with the full code table and cross-model mapping notes. |
| `src/…` TODO issue numbers | Stubs cite draft numbers #1–#10; real issues are #5–#9 and #11–#15 (tracked as issue #10). `regions.py` tests and `prices.py` cite `#N`. |

---
