# Game Mechanics — Technical Reference

This document explains how the three Decarbonator Deck actions translate into
Red Worlds engine inputs and outputs. It is the data contract between the
Red Carbon WordPress front end and this repo.

For the game design assumptions underpinning these choices, see
`docs/design/assumptions.md`.

---

## Overview

Each day, a player sees a scenario: a specific emissions-producing sector in a
specific region for a specific simulation year (e.g. *European residential heating,
Year 3*).

The player engages with the **Decarbonator Deck** on the Red Carbon website and
produces an action result — one of BUILD, SWAP, or REDUCE — which is sent to
Red Worlds.

---

## BUILD

### What the player does
The player chooses a compatible low-carbon technology to build in the scenario's
region (e.g. offshore wind, heat pump manufacturing, nuclear) and a number of units.
Through a series of Deck interactions (civic engagement rolls, builder bonus, etc.)
they produce:

- A **budget** (monetary units, in the IO system's currency)
- A **build period** (simulation years)

### What Red Worlds receives

```json
{
  "action": "build",
  "player_id": "...",
  "region": "Europe and Central Asia",
  "technology": "offshore_wind",
  "budget": 450000,
  "build_years": 5,
  "current_year": 3
}
```

### What Red Worlds does
1. Loads the player's IO system.
2. Spreads `budget / build_years` of CapEx across IO construction sectors for `current_year`.
3. If `current_year` is the final year of the build period, updates the energy mix to
   reflect the new capacity.
4. Rebalances the economy (see `engine/balancing.py`).
5. Saves the updated IO system and returns updated emissions.

---

## SWAP

### What the player does
The player chooses an eco-choice that substitutes one technology for another within
the scenario (e.g. heat pumps for gas heating, vegetarian diet for existing diet).
They roll the Deck to produce:

- A **% rollout** — the fraction of the replaceable share of the scenario that gets swapped

### What Red Worlds receives

```json
{
  "action": "swap",
  "player_id": "...",
  "region": "Europe and Central Asia",
  "from_technology": "gas_heating",
  "to_technology": "heat_pumps",
  "pct_rollout": 0.32
}
```

### What Red Worlds does
1. Loads the player's IO system.
2. Shifts `pct_rollout` of `from_technology`'s final demand share to `to_technology`.
3. Rebalances the economy.
4. Saves the updated IO system and returns updated emissions.

### Notes on the % rollout
The scenario definition (in `data/tech_choices/options.toml`) includes a
`max_replaceable_fraction` for each SWAP option — the maximum share of the scenario
sector that this technology *could* replace, given physical constraints. The Deck
output is a % of that replaceable fraction, not of the full scenario.

---

## REDUCE

### What the player does
The player chooses an eco-sufficiency option (e.g. lower thermostat by 2°C, reduce
excess calorie consumption). They roll the Deck to produce:

- A **% reduction** — how much of the reducible share of the scenario is reduced

### What Red Worlds receives

```json
{
  "action": "reduce",
  "player_id": "...",
  "region": "Europe and Central Asia",
  "sector": "residential_heating",
  "pct_reduction": 0.18
}
```

### What Red Worlds does
1. Loads the player's IO system.
2. Scales down final demand for `sector` in `region` by `pct_reduction`.
3. **Does NOT rebalance** — this is a deliberate post-growth assumption (see `docs/design/assumptions.md`).
4. Saves the updated IO system and returns updated emissions.

---

## Scenario definition (in tech_choices/options.toml)

Each technology/eco-choice in `data/tech_choices/options.toml` has:

```toml
[[build]]
key = "offshore_wind"
label = "Offshore Wind Farm"
compatible_scenarios = ["electricity_generation", "grid_infrastructure"]
regions = ["all"]          # or list specific game regions

[[swap]]
key = "heat_pumps"
label = "Heat Pumps"
replaces = "gas_heating"
compatible_scenarios = ["residential_heating", "commercial_heating"]
max_replaceable_fraction = 0.65   # at most 65% of gas heating can be replaced by heat pumps

[[reduce]]
key = "thermostat_reduction"
label = "Lower Thermostat"
compatible_scenarios = ["residential_heating"]
max_reducible_fraction = 0.20     # at most 20% of residential heating can be saved this way
```

This schema is indicative — the actual structure will evolve as the game is built.

---

## Region names

The 6 amalgamated game regions and their labels (see `data/concordances/region_mapping.csv`):

| Game region label | Approximate coverage |
|---|---|
| Europe and Central Asia | EU, UK, Norway, Switzerland, former Soviet states |
| East Asia and Pacific | China, Japan, South Korea, Australia, SE Asia |
| South Asia | India, Pakistan, Bangladesh, Sri Lanka |
| Sub-Saharan Africa | Africa south of the Sahara |
| Latin America and Caribbean | Mexico, Central and South America |
| North America and Middle East | USA, Canada, Middle East, North Africa |

These regions rotate in a fixed order for each new simulation year.
