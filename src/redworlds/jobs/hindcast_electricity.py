"""Milestone A of the baseline walk: an electricity-only hindcast.

Walks every region's electricity mix from the 2011 table to the observed mix of each
checkpoint year, changing nothing else, and compares the carbon intensity of generation
that comes out with what was observed. Demand, recipes and every other product stay as
2011 has them, so this is a test of one step and of the machinery around it — not yet a
picture of any later year.

What it reports:

- **The technology table.** What the 2011 table says each generation technology is, in each
  region: how much it supplies, its money per kWh, its direct CO2 per kWh, and whether the
  table describes it well enough to scale (``engine.electricity.reliable_technologies``).
- **Per region and checkpoint year.** Modelled direct CO2 intensity of generation beside
  Ember's observed intensity, and the share of generation that had to be represented by a
  stand-in technology.
- **World totals.** World CO2 with only the electricity mix changed, against 2011.

The two intensities are not the same quantity and should not match exactly: the model's is
direct combustion CO2 from the table, Ember's is lifecycle CO2e. For a fossil-heavy grid the
two sit within a few per cent of each other.

Run with ``just hindcast-electricity``. Needs the cached baseline (``just baseline``) and
the prepared electricity tables (``just prepare-electricity``).

References:
  - docs/design/baseline_walk.md — the design
  - docs/plans/03-baseline-walk.md — Milestone A and its results
  - engine/electricity.py — the step itself
"""

from pathlib import Path

import pandas as pd
import pymrio

from redworlds.config import load_config
from redworlds.engine.electricity import (
    electricity_supply_twh,
    implied_prices,
    reliable_technologies,
    shift_electricity_mix,
    substitute_unreliable,
)
from redworlds.engine.io_tables import CO2_STRESSOR, GHG_EXTENSION, recalculate_from_technical_coefficients
from redworlds.jobs.build_baseline import BASELINE_NAME
from redworlds.jobs.prepare_electricity import BASELINE_DATA, load_source_concordance

CHECKPOINT_YEARS: tuple[int, ...] = (2011, 2015, 2019, 2025)

# The CO2 row is in Gg and generation in TWh: one Gg per TWh is one gram per kWh.
GRAMS_PER_KWH_PER_GG_PER_TWH: float = 1.0
GT_PER_GG: float = 1e-6


def load_generation_targets(path: Path | None = None) -> pd.DataFrame:
    """Load the observed-generation ledger rows written by ``prepare_electricity``."""
    return pd.read_csv(path or BASELINE_DATA / "electricity_generation.csv", comment="#")


def target_shares(generation: pd.DataFrame, region: str, year: int) -> dict[str, float]:
    """Return {product: share of generation} for one region and year."""
    rows = generation[(generation["region"] == region) & (generation["year"] == year)]
    if rows.empty:
        raise ValueError(f"no generation targets for {region!r} in {year}")
    twh = rows.set_index("variable")["value"]
    return (twh / twh.sum()).to_dict()


def all_electricity_products(mrio: pymrio.IOSystem) -> list[str]:
    """Every EXIOBASE electricity generation product, including the ones the step leaves alone."""
    return [product for product in mrio.get_sectors() if product.startswith("Electricity")]  # EXIOBASE-specific


def technology_table(mrio: pymrio.IOSystem, products: list[str]) -> pd.DataFrame:
    """Describe each generation technology in each region as the table holds it."""
    co2 = getattr(mrio, GHG_EXTENSION).F.loc[CO2_STRESSOR]
    rows = []
    for region in mrio.get_regions():
        supply = electricity_supply_twh(mrio, region, products)
        prices = implied_prices(mrio, region, supply)
        reliable = reliable_technologies(supply, prices)
        for product in products:
            twh = supply[product]
            rows.append(
                {
                    "region": region,
                    "product": product,
                    "twh": twh,
                    "price_meur_per_twh": prices.get(product),
                    "direct_gco2_per_kwh": float(co2[(region, product)]) / twh if twh > 0.0 else None,
                    "reliable": product in reliable,
                }
            )
    return pd.DataFrame(rows)


def shift_all_regions(
    base: pymrio.IOSystem,
    generation: pd.DataFrame,
    technology_class: dict[str, str],
    year: int,
) -> tuple[pymrio.IOSystem, dict[str, float]]:
    """Shift every region's mix to the observed mix of ``year``, without re-solving.

    Prices and reliability are read from ``base`` (the 2011 table), not from the system
    being changed, so every checkpoint is walked from the same description of each
    technology.

    Returns:
        The uncalculated system, and {region: share of generation represented by a stand-in}.
    """
    products = list(technology_class)
    shifted = base
    substituted: dict[str, float] = {}
    for region in base.get_regions():
        supply = electricity_supply_twh(base, region, products)
        prices = implied_prices(base, region, supply)
        reliable = reliable_technologies(supply, prices)
        shares, substituted[region] = substitute_unreliable(
            target_shares(generation, region, year), reliable, technology_class
        )
        shifted = shift_electricity_mix(shifted, region, shares, prices)
    return shifted, substituted


def walk_electricity(
    base: pymrio.IOSystem,
    generation: pd.DataFrame,
    technology_class: dict[str, str],
    year: int,
) -> tuple[pymrio.IOSystem, dict[str, float]]:
    """Shift every region's mix to the observed mix of ``year`` and re-solve once."""
    shifted, substituted = shift_all_regions(base, generation, technology_class, year)
    return recalculate_from_technical_coefficients(shifted), substituted


def generation_intensity(mrio: pymrio.IOSystem, region: str, products: list[str]) -> tuple[float, float]:
    """Return a region's (generation in TWh, direct CO2 intensity in g per kWh)."""
    co2 = getattr(mrio, GHG_EXTENSION).F.loc[CO2_STRESSOR]
    supply = electricity_supply_twh(mrio, region, products)
    twh = sum(supply.values())
    gg = sum(float(co2[(region, product)]) for product in products)
    return twh, gg / twh * GRAMS_PER_KWH_PER_GG_PER_TWH


def world_co2_gt(mrio: pymrio.IOSystem) -> float:
    """World CO2 in Gt: industry emissions plus households' direct emissions."""
    account = getattr(mrio, GHG_EXTENSION)
    return float(account.F.loc[CO2_STRESSOR].sum() + account.F_Y.loc[CO2_STRESSOR].sum()) * GT_PER_GG


def hindcast(base: pymrio.IOSystem, generation: pd.DataFrame, observed: pd.DataFrame) -> pd.DataFrame:
    """Run the electricity-only walk to each checkpoint and tabulate model against observed."""
    technology_class = load_source_concordance().set_index("exiobase_product")["technology_class"].to_dict()
    products = all_electricity_products(base)
    observed_intensity = observed.set_index(["region", "year"])["intensity_gco2e_per_kwh"]

    rows = []
    for year in CHECKPOINT_YEARS:
        world, substituted = walk_electricity(base, generation, technology_class, year)
        for region in world.get_regions():
            twh, intensity = generation_intensity(world, region, products)
            rows.append(
                {
                    "year": year,
                    "region": region,
                    "model_twh": twh,
                    "model_direct_gco2_per_kwh": intensity,
                    "observed_gco2e_per_kwh": float(observed_intensity[(region, year)]),
                    "stand_in_share": substituted[region],
                    "world_co2_gt": world_co2_gt(world),
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    """Print the technology table and the hindcast for the cached baseline."""
    baseline_path = Path(load_config()["data"]["worlds_path"]) / BASELINE_NAME
    base = pymrio.load_all(baseline_path)
    generation = load_generation_targets()
    observed = pd.read_csv(BASELINE_DATA / "electricity_observed.csv", comment="#")
    products = all_electricity_products(base)

    pd.set_option("display.width", 200)
    technologies = technology_table(base, products)
    print("Technologies the 2011 table cannot scale reliably (others omitted):")
    print(technologies[~technologies["reliable"] & (technologies["twh"] > 0.0)].round(1).to_string(index=False))

    print(f"\nWorld CO2 in the 2011 table as it stands: {world_co2_gt(base):.2f} Gt")
    for region in base.get_regions():
        twh, intensity = generation_intensity(base, region, products)
        print(f"  {region}: {twh:,.0f} TWh at {intensity:.0f} g CO2/kWh direct")

    results = hindcast(base, generation, observed)
    print("\nElectricity-only hindcast (everything except the generation mix held at 2011):")
    print(results.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
