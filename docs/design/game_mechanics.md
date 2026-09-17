# Game Mechanics — Technical Reference

This document explains how a player's action in Red Carbon becomes an input to the Red
Worlds engine, and what the engine sends back. It is the data contract between the game's
front end and this repo.

For the reasoning behind these shapes, see [`red_carbon_contract.md`](red_carbon_contract.md);
for the modelling assumptions, see [`assumptions.md`](assumptions.md).

---

## Overview

Each day a player picks one **tape**: a single large-scale intervention in one game region,
belonging to one of three wings. The game's finale then resolves a push level, a civic
modifier and a dice roll into an **outcome fraction** — how much of the tape's physical
ceiling was actually delivered (0 to 1, occasionally negative for a REDUCE backfire).

| Wing | What the tape does | Money | Matrices touched |
|---|---|---|---|
| **BUILD** | Constructs new low-carbon capacity | Capex injected into investment during build years | Y (GFCF), then A and S after completion |
| **SWAP** | Substitutes one product for another at the same volume | Closed rebalance, total preserved | Y (final demand), later Z for production-side swaps |
| **REDUCE** | Consumes less of a basket of products | Spend leaves the model | Y (final demand) |

The engine never sees dice or civic modifiers. It sees the tape and how much of it landed.

---

## What Red Worlds receives

One job per played tape. The game's finale-resolution module emits it; transport is a
shared job-queue table (see [`architecture.md`](architecture.md)).

```json
{
  "job_id": "…",
  "player_id": "…",
  "tape_id": "eca_nuclear",
  "region_id": 3,
  "outcome_fraction": 0.61,
  "push_level": 3.0,
  "modifier_effects": { "build_time_delta_years": 2, "build_cost_delta": 0.03 }
}
```

`region_id` is the numeric game region (1–7), never a label. `modifier_effects` carries
only the civic modifier's physical consequences (BUILD time and cost deltas); SWAP and
REDUCE modifiers have none.

### The tape record

Everything physical about a tape lives in a committed tape record in
`data/tech_choices/options.toml`, keyed by `tape_id`. The engine reads it; the game
never sends it. Fields:

```toml
[[tape]]
tape_id = "eca_nuclear"
wing = "build"
region_id = 3
scenario_category = "electricity_generation"   # key into concordances/exiobase_to_scenario.csv
technology = "nuclear"
matrix_target = ["GFCF_construction_phase", "A_post_build_energy_mix"]
capacity_gw = 12.0                                # 10 reactors × 1.2 GW
budget_musd_2026_purchaser = 100000               # reference capex, purchaser prices
build_years_reference = 10
capex_split = { construction = 0.40, machinery = 0.42, electrical_machinery = 0.09, business_services = 0.09 }
deployment_curve = "s_curve"                      # how the effect ramps over the remaining years

[[tape]]
tape_id = "eca_electric_vehicle_transition"
wing = "swap"
region_id = 3
scenario_category = "private_road_transport"
from_product = "motor_fuel"
to_product = "electricity"
max_replaceable_fraction = 0.9
deployment_curve = "s_curve"

[[tape]]
tape_id = "eca_buy_less"
wing = "reduce"
region_id = 3
scenario_category = "goods_and_leisure"          # a named basket; see assumptions.md
max_reducible_fraction = 0.05
deployment_curve = "linear_10yr"
```

The schema is indicative and will evolve. Two rules are fixed: **a tape's magnitude is an
engine output** (the game sizes every tape to the same expected abatement, and this engine
reports what physical quantity that takes per region), and **the record never carries
game-side text** (names, pitches, characters stay in the game).

### Derived engine inputs

The action functions take plain physical inputs. The job handler derives them:

| Wing | Engine input | Derivation |
|---|---|---|
| BUILD | `budget`, `build_years` | `budget_musd_2026_purchaser × (1 + cost_delta)`, converted to basic prices; `build_years_reference + time_delta`; the delivered capacity scales with `outcome_fraction` |
| SWAP | `pct_rollout` | `outcome_fraction × max_replaceable_fraction` |
| REDUCE | `pct_reduction` | `outcome_fraction × max_reducible_fraction` |

Function signatures are in `src/redworlds/actions/`.

---

## What Red Worlds does

1. Loads the cached SSP2 baseline world for 2050 (with capital endogenised and the
   Leontief inverse precomputed) and the baseline emissions trajectory 2050–2100.
2. Reads the tape record and derives the engine inputs above.
3. Applies the shock: `apply_build`, `apply_swap` or `apply_reduce`. Y-side shocks reuse
   the cached inverse; coefficient changes trigger a full recalculation.
4. Takes the annual emissions difference against the baseline and runs it through the
   tape's deployment curve (and, for BUILD, the construction-then-operation timing) to
   produce the annual curve and the fifty-year cumulative.
5. Writes `progress_json` after each step so the game can animate, then `result_json`.

For the MVP this is a static comparative: one solve, one delta, scaled through time. See
[`assumptions.md`](assumptions.md) for why.

---

## What Red Worlds sends back

```json
{
  "job_id": "…",
  "status": "done",
  "co2_delta_cumulative_t": -1.02e9,
  "baseline_cumulative_t": 8.47e11,
  "gdp_impact_musd_2026": -125000,
  "jcurve": [
    { "year": 2050, "value": 4.1e6 },
    { "year": 2055, "value": 6.3e6 },
    { "year": 2060, "value": -1.8e7 },
    { "year": 2100, "value": -2.9e7 }
  ],
  "emissions_unit": "kg CO2-eq",
  "brick_equivalent": { "unit": "reactors", "quantity_for_one_brick": 9.6 }
}
```

- `co2_delta_cumulative_t` is signed; negative means abatement. This is the score.
- `jcurve` is the annual delta against baseline in the same unit, in five-year blocks; for
  BUILD it rises during construction then bends down.
- `gdp_impact_musd_2026` is non-zero for REDUCE (and for BUILD under the injection rule).
- `brick_equivalent` is the engine's answer to "how much of this intervention equals one
  brick in this region"; the game uses it to size cover copy.

---

## Region ids

| ID | Game region | EXIOBASE codes (see `data/concordances/region_mapping.csv`) |
|---|---|---|
| 1 | USA and Canada | US, CA |
| 2 | Latin America and the Caribbean | BR, MX, WL |
| 3 | Europe and Central Asia | EU27, GB, NO, CH, TR, RU, WE |
| 4 | Africa and Middle East | ZA, WF, WM |
| 5 | South Asia | IN |
| 6 | Mainland East Asia | CN, KR, TW |
| 7 | South East Asia and Pacific Ocean | JP, AU, ID, WA |

Taiwan sits in region 6, following the game's regions doc (settled 2026-09-17). The CSV
is the engine's source of truth. Rest-of-world blocks: `WA` Asia-Pacific, `WL`
Americas, `WE` Europe, `WF` Africa, `WM` Middle East.
