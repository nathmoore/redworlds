# Data Guide

This directory contains two types of data with very different rules about what
gets committed to the repo.

---

## What IS committed (small reference data)

These files are version-controlled and live in this repo:

| Directory | Contents |
|-----------|---------|
| `concordances/` | Mapping files: EXIOBASE sectors → game scenario categories, EXIOBASE regions → game regions |
| `tech_choices/` | Reference data for BUILD/SWAP/REDUCE technology options and their scenario compatibility |

These files define the game's data contracts. If you want to propose a new technology
option or adjust a sector mapping, edit these files and raise a pull request.

---

## What is NOT committed (large or licensed data)

| Directory | Why gitignored |
|-----------|---------------|
| `exiobase/` | EXIOBASE files are large (hundreds of MB) and licensed CC BY-SA 4.0. Download separately — see below. |
| `worlds/` | Per-player IO tables. These are generated at runtime from EXIOBASE and player actions. |

---

## How to get EXIOBASE

Red Worlds uses [EXIOBASE 3](https://www.exiobase.eu/), a global multi-regional
input-output (MRIO) database.

1. Register at [exiobase.eu](https://www.exiobase.eu/) (free).
2. Download the version you need. Red Worlds targets EXIOBASE 3, ixi (industry-by-industry),
   in pymrio format. The relevant files are typically named `IOT_<year>_ixi.zip`.
3. Extract the files into `data/exiobase/` (this directory is gitignored).
4. Update `config/config.toml` to point at your local copy:

```toml
[data]
exiobase_path = "/path/to/redworlds/data/exiobase"
worlds_path = "/path/to/redworlds/data/worlds"
```

Copy `config/config.example.toml` to `config/config.toml` as your starting point.

---

## Running without EXIOBASE (for developers and contributors)

You do not need EXIOBASE to run the unit tests. All default tests use
`pymrio.load_test()` — a small built-in IO world included with pymrio.

```bash
just test          # runs fine with no data files
```

Integration tests against real EXIOBASE data are marked and skipped by default:

```bash
just test -m integration   # requires config/config.toml + EXIOBASE files
```

---

## Concordance files

### `concordances/exiobase_to_scenario.csv`

Maps game scenario categories (e.g. `residential_heating`) to the EXIOBASE sectors
that represent that activity. One scenario category can span multiple EXIOBASE sectors.

Schema:

| Column | Description |
|--------|-------------|
| `scenario_category` | Game scenario key (e.g. `residential_heating`) |
| `exiobase_sector` | Exact EXIOBASE sector label |
| `weight` | Relative weight of this sector within the scenario (default: 1.0) |
| `notes` | Optional human-readable note or data source reference |

### `concordances/region_mapping.csv`

Maps EXIOBASE country/region codes to the 6 amalgamated game regions.

Schema:

| Column | Description |
|--------|-------------|
| `exiobase_region` | EXIOBASE region code (e.g. `DE`, `CN`, `WA`) |
| `game_region` | Amalgamated game region label |

---

## Tech choices file

### `tech_choices/options.toml`

Defines the technologies and eco-choices available to players for each action type,
with compatible scenario tags and key parameters. See
`docs/design/game_mechanics.md` for the full schema description.
