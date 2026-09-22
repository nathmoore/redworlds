"""Derive fuel-specific shares of EXIOBASE household direct emissions.

The cached table resolves household final energy by purpose but not by fuel. Road energy is
therefore taken from ``Energy Carrier Net TROA`` and converted with IPCC fuel factors. The
gasoline/diesel mix is used only to interpolate between their close combustion factors; it
comes from the table's own household purchases and does not set total road activity.
"""

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, cast

import pymrio

from redworlds.actions.swap import energy_bought
from redworlds.config import load_config
from redworlds.engine.io_tables import CO2_STRESSOR, GHG_STRESSOR, HOUSEHOLDS, emissions_to_tonnes
from redworlds.jobs.build_baseline import BASELINE_NAME

ROAD_ENERGY_STRESSOR = "Energy Carrier Net TROA"
ENERGY_EXTENSION = "satellite"
ENERGY_STRESSOR = "Energy Carrier Supply: Total"

# IPCC 2006 Guidelines, Volume 2, Chapter 3, Tables 3.2.1 and 3.2.2 (kg/TJ).
GASOLINE_FACTORS = {"co2": 69_300.0, "ch4": 3.8, "n2o": 5.7}
DIESEL_FACTORS = {"co2": 74_100.0, "ch4": 3.9, "n2o": 3.9}

# The characterised EXIOBASE row names IPCC 2007 GWP100, whose factors are 25 and 298.
CH4_GWP100 = 25.0
N2O_GWP100 = 298.0


@dataclass(frozen=True)
class RoadDirectEmissions:
    """Auditable road activity, emissions and shares for one consuming region."""

    road_energy_tj: float
    gasoline_energy_fraction: float
    road_co2_t: float
    road_co2e_t: float
    household_direct_co2_t: float
    household_direct_co2e_t: float
    co2_share: float
    co2e_share: float


def road_emissions_from_energy(road_energy_tj: float, gasoline_fraction: float) -> tuple[float, float]:
    """Return road CO₂ and CO₂e tonnes from activity and a gasoline/diesel mix."""
    if road_energy_tj < 0.0:
        raise ValueError(f"road_energy_tj must be non-negative; got {road_energy_tj}")
    if not 0.0 <= gasoline_fraction <= 1.0:
        raise ValueError(f"gasoline_fraction must be in [0, 1]; got {gasoline_fraction}")
    diesel_fraction = 1.0 - gasoline_fraction
    factors = {
        gas: gasoline_fraction * GASOLINE_FACTORS[gas] + diesel_fraction * DIESEL_FACTORS[gas]
        for gas in ("co2", "ch4", "n2o")
    }
    co2_kg = road_energy_tj * factors["co2"]
    co2e_kg = co2_kg + road_energy_tj * factors["ch4"] * CH4_GWP100
    co2e_kg += road_energy_tj * factors["n2o"] * N2O_GWP100
    return co2_kg / 1_000.0, co2e_kg / 1_000.0


def derive_road_direct_emissions(world: pymrio.IOSystem, region: str) -> RoadDirectEmissions:
    """Derive road shares against the characterised household-direct totals."""
    if world.Y is None:
        raise ValueError("derive_road_direct_emissions needs a calculated system")
    columns = (region, [HOUSEHOLDS])
    fuel_energy = {
        product: energy_bought(
            world,
            world.Y.loc[(slice(None), [product]), columns],
            ENERGY_EXTENSION,
            ENERGY_STRESSOR,
        )
        for product in ("Motor Gasoline", "Gas/Diesel Oil")
    }
    fuel_total = sum(fuel_energy.values())
    if fuel_total <= 0.0:
        raise ValueError(f"{region!r} has no positive household petrol or diesel energy")
    gasoline_fraction = fuel_energy["Motor Gasoline"] / fuel_total

    satellite = getattr(world, ENERGY_EXTENSION)
    road_energy_tj = float(satellite.F_Y.loc[ROAD_ENERGY_STRESSOR, (region, HOUSEHOLDS)])
    road_co2_t, road_co2e_t = road_emissions_from_energy(road_energy_tj, gasoline_fraction)

    impacts = cast(Any, world).impacts
    direct_co2 = float(impacts.F_Y.loc[CO2_STRESSOR, (region, HOUSEHOLDS)])
    direct_co2e = float(impacts.F_Y.loc[GHG_STRESSOR, (region, HOUSEHOLDS)])
    household_direct_co2_t = emissions_to_tonnes(world, direct_co2, "impacts", CO2_STRESSOR)
    household_direct_co2e_t = emissions_to_tonnes(world, direct_co2e, "impacts", GHG_STRESSOR)
    co2_share = road_co2_t / household_direct_co2_t
    co2e_share = road_co2e_t / household_direct_co2e_t
    if not 0.0 <= co2_share <= 1.0 or not 0.0 <= co2e_share <= 1.0:
        raise ValueError(f"derived road shares do not reconcile: CO2={co2_share}, CO2e={co2e_share}")
    return RoadDirectEmissions(
        road_energy_tj=road_energy_tj,
        gasoline_energy_fraction=gasoline_fraction,
        road_co2_t=road_co2_t,
        road_co2e_t=road_co2e_t,
        household_direct_co2_t=household_direct_co2_t,
        household_direct_co2e_t=household_direct_co2e_t,
        co2_share=co2_share,
        co2e_share=co2e_share,
    )


def main() -> None:
    """Print the reproducible Region 3 road-emissions derivation as JSON."""
    baseline_path = Path(load_config()["data"]["worlds_path"]) / BASELINE_NAME
    world = pymrio.load_all(baseline_path)
    result = derive_road_direct_emissions(world, "Europe and Central Asia")
    print(json.dumps(asdict(result), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
