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
| `exiobase/` | EXIOBASE files are large (hundreds of MB) and licensed separately. Download — see below. |
| `worlds/` | Per-player IO tables. Generated at runtime from EXIOBASE and player actions. |

---

## How to get EXIOBASE

Red Worlds uses **EXIOBASE 3.8.2**, a global multi-regional input-output (MRIO) database.

### Which file to download

Download `IOT_2011_pxp.zip` from Zenodo:

> **https://zenodo.org/records/5589597**

This is the 2011 product-by-product (pxp) table. We use 2011 because it is the latest
year in 3.8.2 with complete, non-extrapolated supply-use data. Red Worlds performs its
own extrapolation to reach the in-game Baseline year of **2027** and beyond.

### Licence

EXIOBASE 3.8.2 is released under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)
— free to use with attribution and share-alike. More recent EXIOBASE releases exist
(with "now-casted" years) and use CC BY 4.0. Those are fine for personal and research
use but check the terms before redistribution. Version 3.8.2 is what Red Worlds targets.

### Citation

> Stadler, K., Wood, R., Bulavskaya, T., Södersten, C.-J., Simas, M., Schmidt, S.,
> Usubiaga, A., Acosta-Fernández, J., Kuenen, J., Bruckner, M., Giljum, S., Lutter, S.,
> Merciai, S., Schmidt, J. H., Theurl, M. C., Plutzar, C., Kastner, T., Eisenmenger, N.,
> Erb, K.-H., … Tukker, A. (2021). EXIOBASE 3 (3.8.2) [Data set]. Zenodo.
> https://doi.org/10.5281/zenodo.5589597

### Installation

1. Download `IOT_2011_pxp.zip` from the Zenodo link above.
2. Create the directory `data/exiobase/` (it is gitignored — git will never see its contents).
3. Extract the zip into `data/exiobase/`.
4. Copy `config/config.example.toml` to `config/config.toml` and set your paths:

```toml
[data]
exiobase_path = "/path/to/redworlds/data/exiobase"
worlds_path = "/path/to/redworlds/data/worlds"
```

### Monetary units

EXIOBASE values are in **2011 million EUR at basic prices**. Basic prices are producer
prices — what the seller receives — excluding taxes on products and trade/transport
margins. Red Worlds converts these to **2026 constant million USD** for all player-facing
figures (see `src/redworlds/engine/currency.py`).

### Regions

EXIOBASE 3.8.2 covers ~49 countries and regions. Red Worlds aggregates these into **7
game regions**. Our calculations are therefore slightly less granular than results you
would get running EXIOBASE at full country resolution. The region mapping is in
`data/concordances/region_mapping.csv`.

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

Maps EXIOBASE country/region codes to the 7 amalgamated game regions.

Schema:

| Column | Description |
|--------|-------------|
| `exiobase_region` | EXIOBASE region code (ISO-2 for countries, e.g. `DE`, `CN`; special codes for rest-of-world blocks, e.g. `WA`, `WF`) |
| `game_region_id` | Numeric game region ID (1–7) |
| `game_region_name` | Amalgamated game region label |

The 7 game regions are:

| ID | Name |
|----|------|
| 1 | USA and Canada |
| 2 | Latin America and the Caribbean |
| 3 | Europe and Central Asia |
| 4 | Africa and Middle East |
| 5 | South Asia |
| 6 | Mainland East Asia |
| 7 | South East Asia and Pacific Ocean |

---

## Tech choices file

### `tech_choices/options.toml`

Defines the technologies and eco-choices available to players for each action type,
with compatible scenario tags and key parameters. See
`docs/design/game_mechanics.md` for the full schema description.
