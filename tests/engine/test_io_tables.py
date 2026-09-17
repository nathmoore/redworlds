"""Tests for IO table operations (src/redworlds/engine/io_tables.py).

Unit tests use the ``test_mrio`` fixture from conftest.py, pymrio's built-in test world.
Its emissions extension is called ``emissions`` (EXIOBASE calls it ``impacts``) and its
stressor rows are (stressor, compartment) tuples, so every call passes those explicitly.
"""

from typing import Any

import numpy as np
import pymrio
import pytest

from redworlds.engine.io_tables import (
    CONSUMPTION_CATEGORIES,
    GFCF,
    GHG_EXTENSION,
    GHG_STRESSOR,
    get_region_emissions,
    get_sector_emissions,
    recalculate_from_final_demand,
    scale_final_demand,
    shift_sector_share,
)

TEST_EXTENSION = "emissions"
TEST_STRESSOR = ("emission_type1", "air")


def _account(mrio: pymrio.IOSystem, name: str = TEST_EXTENSION) -> Any:
    """pymrio attaches extensions dynamically; fetch one without upsetting the type checker."""
    return getattr(mrio, name)


def _food_demand(mrio: pymrio.IOSystem, region: str) -> np.ndarray:
    """The Y block for ``food`` (from every producer) bought by ``region``."""
    assert mrio.Y is not None
    return mrio.Y.loc[(slice(None), "food"), (region, slice(None))].to_numpy()


def test_scale_final_demand_identity(test_mrio: pymrio.IOSystem) -> None:
    """Scaling by 1.0 returns a new, numerically identical system."""
    result = scale_final_demand(test_mrio, region="reg1", sector="food", factor=1.0)
    assert result is not test_mrio
    assert result.Y is not None and test_mrio.Y is not None
    assert result.Y.equals(test_mrio.Y)


def test_scale_final_demand_zero_removes_the_slice(test_mrio: pymrio.IOSystem) -> None:
    """Factor 0.0 zeroes the product's demand in that region and nothing else."""
    result = scale_final_demand(test_mrio, region="reg1", sector="food", factor=0.0)
    assert result.Y is not None and test_mrio.Y is not None
    assert (_food_demand(result, "reg1") == 0).all()
    assert np.array_equal(_food_demand(result, "reg2"), _food_demand(test_mrio, "reg2"))
    untouched = result.Y.drop(index="food", level="sector")
    assert untouched.equals(test_mrio.Y.drop(index="food", level="sector"))


def test_scale_final_demand_halves_imports_too(test_mrio: pymrio.IOSystem) -> None:
    """The consuming region's column is scaled across every producing region's row."""
    result = scale_final_demand(test_mrio, region="reg1", sector="food", factor=0.5)
    assert np.allclose(_food_demand(result, "reg1"), 0.5 * _food_demand(test_mrio, "reg1"))


def test_scale_final_demand_does_not_mutate_input(test_mrio: pymrio.IOSystem) -> None:
    assert test_mrio.Y is not None
    before = test_mrio.Y.copy()
    scale_final_demand(test_mrio, region="reg1", sector="food", factor=0.0)
    assert test_mrio.Y.equals(before)


def test_scale_final_demand_basket_and_categories(test_mrio: pymrio.IOSystem) -> None:
    """A basket of products can be cut in the consumption columns while investment is untouched."""
    basket = ["food", "mining"]
    result = scale_final_demand(test_mrio, "reg1", basket, factor=0.0, categories=CONSUMPTION_CATEGORIES)
    assert result.Y is not None and test_mrio.Y is not None
    rows = (slice(None), basket)
    assert result.Y.loc[rows, ("reg1", list(CONSUMPTION_CATEGORIES))].to_numpy().sum() == 0.0
    assert result.Y.loc[rows, ("reg1", GFCF)].equals(test_mrio.Y.loc[rows, ("reg1", GFCF)])


def test_recalculate_keeps_leontief_inverse_and_recomputes_flows(test_mrio: pymrio.IOSystem) -> None:
    """The Y-side path reuses L and lowers output and emissions when demand falls."""
    cut = scale_final_demand(test_mrio, "reg1", "food", factor=0.5)
    result = recalculate_from_final_demand(cut)
    assert result.L is not None and test_mrio.L is not None and result.x is not None and test_mrio.x is not None
    assert np.allclose(result.L.to_numpy(), test_mrio.L.to_numpy())
    assert result.x.to_numpy().sum() < test_mrio.x.to_numpy().sum()
    assert result.Y is not None
    assert np.allclose(result.x.to_numpy().ravel(), (result.L @ result.Y.sum(axis=1)).to_numpy())


def test_recalculate_of_unchanged_system_is_identity(test_mrio: pymrio.IOSystem) -> None:
    result = recalculate_from_final_demand(test_mrio)
    assert np.allclose(_account(result).D_cba.to_numpy(), _account(test_mrio).D_cba.to_numpy())


def test_get_sector_emissions_non_negative_and_consumption_based(test_mrio: pymrio.IOSystem) -> None:
    """Sector emissions read from D_cba, so they equal pymrio's own consumption account."""
    value = get_sector_emissions(test_mrio, "reg1", "food", TEST_EXTENSION, TEST_STRESSOR)
    assert value >= 0.0
    assert value == pytest.approx(_account(test_mrio).D_cba.loc[TEST_STRESSOR, ("reg1", "food")])


def test_get_region_emissions_matches_pymrio_regional_account(test_mrio: pymrio.IOSystem) -> None:
    value = get_region_emissions(test_mrio, "reg1", TEST_EXTENSION, TEST_STRESSOR)
    assert value == pytest.approx(_account(test_mrio).D_cba_reg.loc[TEST_STRESSOR, "reg1"])


def test_emissions_fall_when_demand_falls(test_mrio: pymrio.IOSystem) -> None:
    """Halving reg1's food demand halves the embodied emissions of that slice and lowers the footprint."""
    result = recalculate_from_final_demand(scale_final_demand(test_mrio, "reg1", "food", factor=0.5))
    before = get_sector_emissions(test_mrio, "reg1", "food", TEST_EXTENSION, TEST_STRESSOR)
    after = get_sector_emissions(result, "reg1", "food", TEST_EXTENSION, TEST_STRESSOR)
    assert after == pytest.approx(0.5 * before)
    assert get_region_emissions(result, "reg1", TEST_EXTENSION, TEST_STRESSOR) < get_region_emissions(
        test_mrio, "reg1", TEST_EXTENSION, TEST_STRESSOR
    )


def test_emissions_default_labels_are_exiobase(test_mrio: pymrio.IOSystem) -> None:
    """The defaults name EXIOBASE's impacts account, so the test world must pass its own labels."""
    assert GHG_EXTENSION == "impacts"
    assert GHG_STRESSOR.startswith("GHG emissions (GWP100)")
    with pytest.raises(AttributeError):
        get_region_emissions(test_mrio, "reg1")


@pytest.mark.skip(reason="shift_sector_share not yet implemented — see docs/backlog.md")
def test_shift_sector_share_conserves_total(test_mrio: pymrio.IOSystem) -> None:
    """Total demand across from_sector + to_sector should be unchanged after a shift."""
    shift_sector_share(test_mrio, "reg1", "food", "mining", 0.1)


@pytest.mark.integration
def test_exiobase_ghg_labels_exist(exiobase_mrio: pymrio.IOSystem) -> None:
    """The EXIOBASE-specific default labels resolve on the real 2011 table."""
    assert get_region_emissions(exiobase_mrio, "DE") > 0.0
    assert _account(exiobase_mrio, GHG_EXTENSION).unit.loc[GHG_STRESSOR, "unit"] == "kg CO2 eq."
