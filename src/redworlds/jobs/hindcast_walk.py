"""The walk so far, run as a hindcast: economy size, spending mix, electricity.

Builds each checkpoint year from the 2011 table three times, adding one step each time, and
compares world and regional CO2 with what was observed:

- **Economy size only.** Each region's final demand scaled by its real GDP growth; every
  recipe and emission rate as in 2011. This is "the 2011 world, bigger".
- **With spending mix.** The same, with each region's household basket moved by the growth
  in its income per head (real GDP per person) and published income elasticities.
- **With electricity mix.** The same again, with each region's generation walked to the
  observed mix of that year.

The gap that remains between the third run and the observed figure is what the steps not
yet built have to explain: efficiency and productivity, electrification of transport and
heat, and industry.

Observed CO2 is the Global Carbon Budget's fossil and industrial series as distributed in
Our World in Data's CO2 dataset, read from a local download and not committed. Regional
figures are territorial and leave out international aviation and shipping, which the table
books to the regions that operate them; the world figure includes them.

Run with ``just hindcast-walk``. Needs the cached baseline, the prepared tables in
``data/baseline/`` and the CO2 download described in data/README.md.

References:
  - docs/design/baseline_walk.md — the design
  - docs/design/how_we_predict_the_future.md — what goes in, and what is assumed
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
from redworlds.engine.spending import shift_spending_mix
from redworlds.jobs.build_baseline import BASELINE_NAME
from redworlds.jobs.hindcast_electricity import load_generation_targets, shift_all_regions
from redworlds.jobs.prepare_economy import growth_factors
from redworlds.jobs.prepare_electricity import BASELINE_DATA, REPO_ROOT, load_country_regions, load_source_concordance
from redworlds.jobs.prepare_spending import product_elasticities

OBSERVED_CO2_RAW = REPO_ROOT / "data" / "owid" / "owid-co2-data.csv"
CHECKPOINT_YEARS: tuple[int, ...] = (2015, 2019, 2025)
BASE_YEAR: int = 2011
GT_PER_GG: float = 1e-6
GT_PER_MT: float = 1e-3
WORLD: str = "World"
# The three runs, each adding one step to the one before.
RUNS: tuple[str, ...] = ("economy_only", "with_spending", "with_electricity")


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


def income_changes(economy: pd.DataFrame, year: int, base_year: int = BASE_YEAR) -> dict[str, float]:
    """Return {region: relative change in real GDP per person} between two ledger years."""
    gdp = growth_factors(economy, year, base_year, "GDP")
    population = growth_factors(economy, year, base_year, "Population")
    return {region: gdp[region] / population[region] - 1.0 for region in gdp}


def shift_all_spending(
    mrio: pymrio.IOSystem,
    elasticities: dict[str, dict[str, float]],
    changes: dict[str, float],
) -> pymrio.IOSystem:
    """Apply the spending-mix step to every region that has both elasticities and an income change."""
    result = mrio
    for region, change in changes.items():
        if region in elasticities:
            result = shift_spending_mix(result, region, elasticities[region], change)
    return result


def hindcast(
    base: pymrio.IOSystem,
    economy: pd.DataFrame,
    generation: pd.DataFrame,
    observed: pd.DataFrame,
    elasticities: dict[str, dict[str, float]],
    years: tuple[int, ...] = CHECKPOINT_YEARS,
) -> pd.DataFrame:
    """Build each checkpoint year three ways and tabulate modelled against observed CO2."""
    technology_class = load_source_concordance().set_index("exiobase_product")["technology_class"].to_dict()
    observed_by = observed.set_index(["region", "year"])["co2_gt"]

    def tabulate(year: int, runs: dict[str, dict[str, float]]) -> list[dict]:
        runs = {name: co2 | {WORLD: sum(co2.values())} for name, co2 in runs.items()}
        regions = next(iter(runs.values()))
        return [
            {"year": year, "region": region}
            | {f"{name}_gt": co2[region] for name, co2 in runs.items()}
            | {"observed_gt": observed_by.get((region, year))}
            for region in regions
        ]

    base_co2 = production_co2_gt(base)
    rows = tabulate(BASE_YEAR, dict.fromkeys(RUNS, base_co2))
    for year in years:
        factors = growth_factors(economy, year, BASE_YEAR)
        changes = income_changes(economy, year)
        economy_only = scale_economies(base, factors)
        with_spending = shift_all_spending(economy_only, elasticities, changes)
        shifted, _ = shift_all_regions(base, generation, technology_class, year)
        with_electricity = shift_all_spending(scale_economies(shifted, factors), elasticities, changes)
        solved = (
            recalculate_from_final_demand(economy_only),
            recalculate_from_final_demand(with_spending),
            recalculate_from_technical_coefficients(with_electricity),
        )
        rows += tabulate(year, dict(zip(RUNS, map(production_co2_gt, solved), strict=True)))
    return pd.DataFrame(rows)


def main() -> None:
    """Print the hindcast for the cached baseline."""
    if not OBSERVED_CO2_RAW.exists():
        raise SystemExit(f"observed CO2 download not found at {OBSERVED_CO2_RAW} — see data/README.md")
    base = pymrio.load_all(Path(load_config()["data"]["worlds_path"]) / BASELINE_NAME)
    economy = pd.read_csv(BASELINE_DATA / "economy.csv", comment="#")
    observed = observed_co2_gt(pd.read_csv(OBSERVED_CO2_RAW), load_country_regions())

    results = hindcast(base, economy, load_generation_targets(), observed, product_elasticities())
    results["gap_to_observed"] = results["with_electricity_gt"] / results["observed_gt"] - 1.0
    pd.set_option("display.width", 200)
    print("CO2 in Gt. The 2011 rows are the table as it stands.")
    print(results.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
