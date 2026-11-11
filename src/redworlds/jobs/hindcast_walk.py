"""The walk so far, run as a hindcast: economy size, then economy size plus electricity.

Builds each checkpoint year from the 2011 table twice and compares world and regional CO2
with what was observed:

- **Economy size only.** Each region's final demand scaled by its real GDP growth; every
  recipe and emission rate as in 2011. This is "the 2011 world, bigger".
- **Economy size and electricity mix.** The same, with each region's generation walked to
  the observed mix of that year.

The gap that remains between the second run and the observed figure is what the steps not
yet built have to explain: efficiency and productivity, electrification of transport and
heat, industry, and changes in what households buy.

Observed CO2 is the Global Carbon Budget's fossil and industrial series as distributed in
Our World in Data's CO2 dataset, read from a local download and not committed. Regional
figures are territorial and leave out international aviation and shipping, which the table
books to the regions that operate them; the world figure includes them.

Run with ``just hindcast-walk``. Needs the cached baseline, both prepared tables in
``data/baseline/`` and the CO2 download described in data/README.md.

References:
  - docs/design/baseline_walk.md — the design
  - docs/plans/03-baseline-walk.md — results
"""

from pathlib import Path

import pandas as pd
import pymrio

from redworlds.config import load_config
from redworlds.engine.economy import scale_economies
from redworlds.engine.io_tables import (
    CO2_STRESSOR,
    GHG_EXTENSION,
    recalculate_from_final_demand,
    recalculate_from_technical_coefficients,
)
from redworlds.jobs.build_baseline import BASELINE_NAME
from redworlds.jobs.hindcast_electricity import load_generation_targets, shift_all_regions
from redworlds.jobs.prepare_economy import growth_factors
from redworlds.jobs.prepare_electricity import BASELINE_DATA, REPO_ROOT, load_country_regions, load_source_concordance

OBSERVED_CO2_RAW = REPO_ROOT / "data" / "owid" / "owid-co2-data.csv"
CHECKPOINT_YEARS: tuple[int, ...] = (2015, 2019, 2025)
BASE_YEAR: int = 2011
GT_PER_GG: float = 1e-6
GT_PER_MT: float = 1e-3
WORLD: str = "World"


def production_co2_gt(mrio: pymrio.IOSystem) -> dict[str, float]:
    """Return {region: CO2 emitted in the region, in Gt}: its industries plus its households."""
    account = getattr(mrio, GHG_EXTENSION)
    industry = account.F.loc[CO2_STRESSOR].groupby(level=0).sum()
    households = account.F_Y.loc[CO2_STRESSOR].groupby(level=0).sum()
    return ((industry + households) * GT_PER_GG).to_dict()


def observed_co2_gt(raw: pd.DataFrame, country_regions: dict[str, str]) -> pd.DataFrame:
    """Sum observed country CO2 into game regions, with the world total beside them.

    Args:
        raw: Our World in Data's CO2 table: ``country``, ``iso_code``, ``year``, ``co2`` (Mt).
        country_regions: {ISO3: game region}.

    Returns:
        One row per region (and ``"World"``) and year, with ``co2_gt``. A region-year is
        present only if at least one of its countries has a figure.
    """
    countries = raw[raw["iso_code"].isin(country_regions) & raw["co2"].notna()]
    regional = countries.groupby([countries["iso_code"].map(country_regions), "year"])["co2"].sum()
    regional = regional.rename_axis(index=["region", "year"])
    world = raw[(raw["country"] == WORLD) & raw["co2"].notna()].set_index("year")["co2"]
    world.index = pd.MultiIndex.from_product([[WORLD], world.index], names=["region", "year"])
    return (pd.concat([regional, world]) * GT_PER_MT).rename("co2_gt").reset_index()


def hindcast(
    base: pymrio.IOSystem,
    economy: pd.DataFrame,
    generation: pd.DataFrame,
    observed: pd.DataFrame,
    years: tuple[int, ...] = CHECKPOINT_YEARS,
) -> pd.DataFrame:
    """Build each checkpoint year both ways and tabulate modelled against observed CO2."""
    technology_class = load_source_concordance().set_index("exiobase_product")["technology_class"].to_dict()
    observed_by = observed.set_index(["region", "year"])["co2_gt"]

    def tabulate(year: int, economy_only: dict[str, float], with_electricity: dict[str, float]) -> list[dict]:
        world = {WORLD: sum(economy_only.values())}, {WORLD: sum(with_electricity.values())}
        economy_only, with_electricity = economy_only | world[0], with_electricity | world[1]
        return [
            {
                "year": year,
                "region": region,
                "economy_only_gt": economy_only[region],
                "with_electricity_gt": with_electricity[region],
                "observed_gt": observed_by.get((region, year)),
            }
            for region in economy_only
        ]

    base_co2 = production_co2_gt(base)
    rows = tabulate(BASE_YEAR, base_co2, base_co2)
    for year in years:
        factors = growth_factors(economy, year, BASE_YEAR)
        economy_only = recalculate_from_final_demand(scale_economies(base, factors))
        shifted, _ = shift_all_regions(base, generation, technology_class, year)
        both = recalculate_from_technical_coefficients(scale_economies(shifted, factors))
        rows += tabulate(year, production_co2_gt(economy_only), production_co2_gt(both))
    return pd.DataFrame(rows)


def main() -> None:
    """Print the hindcast for the cached baseline."""
    if not OBSERVED_CO2_RAW.exists():
        raise SystemExit(f"observed CO2 download not found at {OBSERVED_CO2_RAW} — see data/README.md")
    base = pymrio.load_all(Path(load_config()["data"]["worlds_path"]) / BASELINE_NAME)
    economy = pd.read_csv(BASELINE_DATA / "economy.csv", comment="#")
    observed = observed_co2_gt(pd.read_csv(OBSERVED_CO2_RAW), load_country_regions())

    results = hindcast(base, economy, load_generation_targets(), observed)
    results["gap_to_observed"] = results["with_electricity_gt"] / results["observed_gt"] - 1.0
    pd.set_option("display.width", 200)
    print("CO2 in Gt. The 2011 rows are the table as it stands.")
    print(results.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
