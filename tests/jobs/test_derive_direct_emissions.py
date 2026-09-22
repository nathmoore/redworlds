"""Tests for the reproducible household-road emissions apportionment."""

from pathlib import Path

import pymrio
import pytest

from redworlds.config import load_config
from redworlds.jobs.build_baseline import BASELINE_NAME
from redworlds.jobs.derive_direct_emissions import derive_road_direct_emissions, road_emissions_from_energy


def test_road_emissions_interpolate_fuel_factors() -> None:
    gasoline_co2, gasoline_co2e = road_emissions_from_energy(1.0, 1.0)
    diesel_co2, diesel_co2e = road_emissions_from_energy(1.0, 0.0)

    assert gasoline_co2 == pytest.approx(69.3)
    assert diesel_co2 == pytest.approx(74.1)
    assert gasoline_co2e > gasoline_co2
    assert diesel_co2e > diesel_co2


@pytest.mark.parametrize("energy,mix", [(-1.0, 0.5), (1.0, -0.1), (1.0, 1.1)])
def test_road_emissions_reject_invalid_activity(energy: float, mix: float) -> None:
    with pytest.raises(ValueError):
        road_emissions_from_energy(energy, mix)


@pytest.mark.integration
def test_region_three_road_shares_reconcile_to_direct_totals() -> None:
    path = Path(load_config()["data"]["worlds_path"]) / BASELINE_NAME
    if not path.exists():
        pytest.skip(f"no cached baseline at {path} — run `just baseline`")
    result = derive_road_direct_emissions(pymrio.load_all(path), "Europe and Central Asia")

    assert result.road_energy_tj == pytest.approx(7_939_653.0)
    assert result.co2_share == pytest.approx(0.5422926887)
    assert result.co2e_share == pytest.approx(0.5365000495)
    assert result.road_co2_t < result.road_co2e_t
