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

`concordances/exiobase_to_scenario.csv` carries an optional `mean_life_years` column. It is
populated only for the product-lifetime basket and is the input to
`extra_years / (mean_life_years + extra_years)`; the `weight` column remains the derived
share at that tape's four-year ceiling.

---

## What is NOT committed (large or licensed data)

| Directory | Why gitignored |
|-----------|---------------|
| `exiobase/` | EXIOBASE files are large (hundreds of MB) and licensed separately. Download — see below. |
| `ember/` | The raw Ember electricity download (16 MB). Small derived tables are committed in `baseline/`. |
| `worldbank/` | Raw World Bank GDP and population downloads. A small derived table is committed in `baseline/`. |
| `bjelle2021/` | Two workbooks from the supplement to Bjelle et al. 2021. Small derived tables are committed in `baseline/` and `concordances/`. |
| `owid/` | Observed CO₂ by country (Our World in Data's distribution of the Global Carbon Budget). Read as a check only; nothing derived from it is committed. |
| `worlds/` | The cached 2050 baseline and (phase 2) per-player IO tables. Generated from EXIOBASE. |

---

## How to get EXIOBASE

Red Worlds uses **EXIOBASE 3.8.2**, a global multi-regional input-output (MRIO) database.

### Which file to download

Download `IOT_2011_pxp.zip` from Zenodo:

> **https://zenodo.org/records/5589597**

This is the 2011 product-by-product (pxp) table. We use 2011 because it is the latest
year in 3.8.2 with complete, non-extrapolated supply-use data. Red Worlds extrapolates it
under the CMIP7 *Medium* scenario to the in-game year of **2050** and on to 2100.

### Capital use matrices

Red Worlds endogenises capital in the baseline (see `docs/design/assumptions.md`). Download
the 2011 product-by-product capital use matrix from Zenodo:

> **https://zenodo.org/records/7073276** — file `Kbar_exio_v3_8_2_2011_cfc_pxp.mat`

Wood, R. & Södersten, C.-J. (2021). Capital use matrices for EXIOBASE v3.8.2 [Data set].
Zenodo. Licence CC-BY-4.0. Put it in `data/exiobase/capital/` (gitignored) and set
`capital_use_path` in `config/config.toml`.

### Licence

EXIOBASE 3.8.2 is released under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)
— free to use with attribution and share-alike. Version 3.8.2 is what Red Worlds targets.
EXIOBASE 3.9 and later are released under a different, non-commercial licence (stated on
their Zenodo records, checked 2026-11-11) and are not used here.

---

## Baseline walk data (`baseline/`, committed)

Small tables the baseline walk reads, each derived from an open source by a job in
`src/redworlds/jobs/` and committed with attribution. See
`docs/plans/03-baseline-walk.md` § Sources for the licence test a source has to pass before
its data may be committed here.

| File | What it holds | Derived from | Job |
|---|---|---|---|
| `electricity_generation.csv` | Observed TWh by game region, year and EXIOBASE electricity product, 2011–2025 | Ember yearly electricity data, CC BY 4.0 | `just prepare-electricity` |
| `electricity_observed.csv` | Observed generation, power emissions and emissions intensity by game region and year | same | same |
| `economy.csv` | Real GDP and population by game region and year, 2011–2025 | World Bank World Development Indicators, CC BY 4.0 | `just prepare-economy` |
| `income_elasticities.csv` | Income elasticity of household spending, and 2011 budget share, by game region and consumption category | Bjelle et al. 2021 supplement, CC BY 4.0; budget shares from EXIOBASE 3.8.2, CC BY-SA 4.0 | `just prepare-spending` |
| `intensity_outliers.csv` | Region-product cells whose emission intensity is far from the world's: a diagnostic, not an input | EXIOBASE 3.8.2 (the cached baseline), CC BY-SA 4.0 | `just diagnose-intensities` |

The same job writes `concordances/exiobase_to_consumption_category.csv`, which assigns each
EXIOBASE product to one of the paper's fifteen consumption categories.

All of these files are comma-separated with the column header on the first line and `#` comment
lines after it; read them with `pandas.read_csv(path, comment="#")`.

### How to get the Ember data

Download `release_generation_yearly_global.csv` (about 16 MB) from Ember's yearly
electricity data page, https://ember-energy.org/data/yearly-electricity-data/ , into
`data/ember/` (gitignored). Then run `just prepare-electricity`.

> Ember. *Yearly electricity data.* https://ember-energy.org — licensed CC BY 4.0.

### How to get the World Bank data

Two indicators from the World Bank's open API, saved into `data/worldbank/` (gitignored)
under the indicator's code:

```sh
cd data/worldbank
for code in NY.GDP.MKTP.KD SP.POP.TOTL; do
  curl -L -o "$code.json" \
    "https://api.worldbank.org/v2/country/all/indicator/$code?format=json&date=2011:2025&per_page=20000"
done
```

Then run `just prepare-economy`.

> World Bank. *World Development Indicators*: GDP (constant 2015 US$), NY.GDP.MKTP.KD, and
> Population, total, SP.POP.TOTL. https://data.worldbank.org — licensed CC BY 4.0.

### How to get the income elasticities

The supplementary data to Bjelle et al. 2021 is one zip file, linked from the article page
under *Appendix A. Supplementary data* (https://doi.org/10.1016/j.eneco.2021.105114; the
article and its supplement are open access under CC BY 4.0). Unzip it and put two of its
workbooks into `data/bjelle2021/` (gitignored):

- `SI_regression_data.xlsx` — sheet `eps_income` holds the income elasticities
- `SI_concordances.xlsx` — sheet `Products` maps EXIOBASE products to categories

Then run `just prepare-spending`. It also reads `Y.txt` from the EXIOBASE download, to weight
countries into game regions by what their households spend.

> Bjelle, E. L., Wiebe, K. S., Többen, J., Tisserant, A., Ivanova, D., Vita, G., & Wood, R.
> (2021). Future changes in consumption: The income effect on greenhouse gas emissions.
> *Energy Economics*, 95, 105114. https://doi.org/10.1016/j.eneco.2021.105114 — CC BY 4.0.

### How to get the observed CO₂ series

`just hindcast-walk` compares the walk with observed emissions. Download
`owid-co2-data.csv` from https://github.com/owid/co2-data into `data/owid/` (gitignored).
Our World in Data publishes its own work under CC BY 4.0; the fossil CO₂ figures in this
file come from the Global Carbon Budget, whose own terms have not been checked here, so the
file is read locally and nothing derived from it is committed.

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
capital_use_path = "/path/to/redworlds/data/exiobase/capital/Kbar_exio_v3_8_2_2011_cfc_pxp.mat"
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
