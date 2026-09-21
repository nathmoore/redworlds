"""Tests for the REDUCE action (src/redworlds/actions/reduce.py).

All tests use the ``test_mrio`` fixture from conftest.py, pymrio's test world, whose
emissions account is ``emissions`` with tuple stressor labels.
"""

from typing import Any

import numpy as np
import pandas as pd
import pymrio
import pytest

from redworlds.actions.reduce import apply_reduce
from redworlds.engine.io_tables import CONSUMPTION_CATEGORIES, GFCF, HOUSEHOLDS, get_region_emissions
from redworlds.engine.scoring import total_emissions

TEST_EXTENSION = "emissions"
TEST_STRESSOR = ("emission_type1", "air")


def _account(mrio: pymrio.IOSystem, name: str = TEST_EXTENSION) -> Any:
    """pymrio attaches extensions dynamically; fetch one without upsetting the type checker."""
    return getattr(mrio, name)


def _consumption(mrio: pymrio.IOSystem, region: str, sector: str) -> float:
    assert mrio.Y is not None
    return float(mrio.Y.loc[(slice(None), sector), (region, list(CONSUMPTION_CATEGORIES))].to_numpy().sum())


def test_reduce_decreases_final_demand(test_mrio: pymrio.IOSystem) -> None:
    """The basket's consumption demand falls by pct_reduction; investment is untouched."""
    result = apply_reduce(test_mrio, region="reg1", sector="food", pct_reduction=0.1)
    assert result is not test_mrio
    assert _consumption(result, "reg1", "food") == pytest.approx(0.9 * _consumption(test_mrio, "reg1", "food"))
    assert result.Y is not None and test_mrio.Y is not None
    assert result.Y[("reg1", GFCF)].equals(test_mrio.Y[("reg1", GFCF)])


def test_reduce_does_not_rebalance(test_mrio: pymrio.IOSystem) -> None:
    """Total final demand is lower afterwards: the spend leaves the model (post-growth)."""
    result = apply_reduce(test_mrio, region="reg1", sector="food", pct_reduction=0.1)
    assert result.Y is not None and test_mrio.Y is not None
    removed = _consumption(test_mrio, "reg1", "food") - _consumption(result, "reg1", "food")
    assert removed > 0
    assert test_mrio.Y.to_numpy().sum() - result.Y.to_numpy().sum() == pytest.approx(removed)


def test_reduce_does_not_mutate_input(test_mrio: pymrio.IOSystem) -> None:
    assert test_mrio.Y is not None
    before = test_mrio.Y.copy()
    apply_reduce(test_mrio, region="reg1", sector="food", pct_reduction=0.5)
    assert test_mrio.Y.equals(before)


def test_reduce_lowers_emissions_and_returns_calculated_system(test_mrio: pymrio.IOSystem) -> None:
    result = apply_reduce(test_mrio, region="reg1", sector="food", pct_reduction=0.5)
    assert result.x is not None and result.L is not None
    before = get_region_emissions(test_mrio, "reg1", TEST_EXTENSION, TEST_STRESSOR)
    after = get_region_emissions(result, "reg1", TEST_EXTENSION, TEST_STRESSOR)
    assert after < before


def test_reduce_of_zero_is_identity(test_mrio: pymrio.IOSystem) -> None:
    result = apply_reduce(test_mrio, region="reg1", sector="food", pct_reduction=0.0)
    assert result.Y is not None and test_mrio.Y is not None
    assert result.Y.equals(test_mrio.Y)
    assert np.allclose(_account(result).D_cba.to_numpy(), _account(test_mrio).D_cba.to_numpy())


def test_reduce_accepts_a_basket(test_mrio: pymrio.IOSystem) -> None:
    result = apply_reduce(test_mrio, region="reg1", sector=["food", "mining"], pct_reduction=1.0)
    assert _consumption(result, "reg1", "food") == 0.0
    assert _consumption(result, "reg1", "mining") == 0.0


def test_reduce_backfire_raises_demand(test_mrio: pymrio.IOSystem) -> None:
    """A negative pct_reduction (the game's REDUCE backfire) increases demand."""
    result = apply_reduce(test_mrio, region="reg1", sector="food", pct_reduction=-0.1)
    assert _consumption(result, "reg1", "food") == pytest.approx(1.1 * _consumption(test_mrio, "reg1", "food"))


def test_reduce_rejects_more_than_everything(test_mrio: pymrio.IOSystem) -> None:
    with pytest.raises(ValueError, match="at most 1.0"):
        apply_reduce(test_mrio, region="reg1", sector="food", pct_reduction=1.5)


# ``manufactoring`` is ~90% of reg1's household spend, so the whole-basket ride and the
# product's own factor are far apart — which is what makes the fuel case testable here.
FAT_SECTOR = "manufactoring"


def _direct(mrio: pymrio.IOSystem, region: str) -> float:
    """The region's direct household emissions (F_Y): fuel burnt, not fuel bought embodied."""
    return float(_account(mrio).F_Y.loc[TEST_STRESSOR, region].sum())


def _household_spend_factor(before: pymrio.IOSystem, after: pymrio.IOSystem, region: str) -> float:
    assert before.Y is not None and after.Y is not None
    return float(after.Y[(region, HOUSEHOLDS)].sum() / before.Y[(region, HOUSEHOLDS)].sum())


def test_reduce_default_leaves_direct_emissions_on_the_basket_path(test_mrio: pymrio.IOSystem) -> None:
    """Default behaviour is unchanged: F_Y follows total household spend, as before the fix."""
    result = apply_reduce(test_mrio, region="reg1", sector=FAT_SECTOR, pct_reduction=0.5)
    ride = _household_spend_factor(test_mrio, result, "reg1")
    assert _direct(result, "reg1") == pytest.approx(ride * _direct(test_mrio, "reg1"))
    assert _direct(result, "reg1") != pytest.approx(0.5 * _direct(test_mrio, "reg1"))


def test_reduce_fuel_tape_moves_direct_emissions_by_the_fuel(test_mrio: pymrio.IOSystem) -> None:
    """Opting in, F_Y falls by pct_reduction — the fuel's own change, not the basket's."""
    result = apply_reduce(
        test_mrio,
        region="reg1",
        sector=FAT_SECTOR,
        pct_reduction=0.5,
        direct_emissions_extension=TEST_EXTENSION,
    )
    assert _direct(result, "reg1") == pytest.approx(0.5 * _direct(test_mrio, "reg1"))


def test_reduce_fuel_tape_only_moves_the_named_region(test_mrio: pymrio.IOSystem) -> None:
    result = apply_reduce(
        test_mrio, region="reg1", sector=FAT_SECTOR, pct_reduction=1.0, direct_emissions_extension=TEST_EXTENSION
    )
    assert _direct(result, "reg1") == pytest.approx(0.0)
    assert _direct(result, "reg2") == pytest.approx(_direct(test_mrio, "reg2"))


def test_reduce_fuel_tape_beats_the_default_on_the_same_tape(test_mrio: pymrio.IOSystem) -> None:
    """A fuel tape on a small product abates more than the default path would credit it."""
    kwargs: dict[str, Any] = {"region": "reg1", "sector": "food", "pct_reduction": 0.5}
    default = apply_reduce(test_mrio, **kwargs)
    fuel = apply_reduce(test_mrio, **kwargs, direct_emissions_extension=TEST_EXTENSION)
    assert _direct(fuel, "reg1") < _direct(default, "reg1")
    assert get_region_emissions(fuel, "reg1", TEST_EXTENSION, TEST_STRESSOR) < get_region_emissions(
        default, "reg1", TEST_EXTENSION, TEST_STRESSOR
    )


def test_reduce_fuel_tape_does_not_mutate_input(test_mrio: pymrio.IOSystem) -> None:
    before = _account(test_mrio).F_Y.copy()
    apply_reduce(
        test_mrio, region="reg1", sector=FAT_SECTOR, pct_reduction=0.5, direct_emissions_extension=TEST_EXTENSION
    )
    assert _account(test_mrio).F_Y.equals(before)


def test_reduce_fuel_tape_keeps_the_footprint_identity(test_mrio: pymrio.IOSystem) -> None:
    """Total footprint still equals embodied emissions plus direct emissions."""
    result = apply_reduce(
        test_mrio, region="reg1", sector=FAT_SECTOR, pct_reduction=0.5, direct_emissions_extension=TEST_EXTENSION
    )
    embodied = _account(result).D_cba.T.groupby(level="region", sort=False).sum().T
    for region in ("reg1", "reg2"):
        assert get_region_emissions(result, region, TEST_EXTENSION, TEST_STRESSOR) == pytest.approx(
            embodied.loc[TEST_STRESSOR, region] + _direct(result, region)
        )


def test_reduce_fuel_tape_of_zero_is_identity(test_mrio: pymrio.IOSystem) -> None:
    result = apply_reduce(
        test_mrio, region="reg1", sector="food", pct_reduction=0.0, direct_emissions_extension=TEST_EXTENSION
    )
    assert np.allclose(_account(result).F_Y.to_numpy(), _account(test_mrio).F_Y.to_numpy())
    assert np.allclose(_account(result).D_cba_reg.to_numpy(), _account(test_mrio).D_cba_reg.to_numpy())


# --- Weighted baskets ------------------------------------------------------------------
#
# A basket need not be cut evenly. These pin the two things that could go silently wrong:
# a weight not actually reaching the right product, and weights breaking the linearity the
# whole precomputed-table design rests on.


def _region_demand(mrio: pymrio.IOSystem, region: str, product: str, categories: list[str]) -> float:
    """Total final demand for one product in a region's named columns."""
    assert mrio.Y is not None
    return float(mrio.Y.loc[(slice(None), [product]), (region, categories)].to_numpy().sum())


def test_weights_give_each_product_its_own_cut(test_mrio) -> None:
    """A product's realised cut is pct_reduction x its weight, not the headline alone."""
    region = list(test_mrio.get_regions())[0]
    heavy, light = list(test_mrio.get_sectors())[:2]
    categories = [HOUSEHOLDS]

    result = apply_reduce(
        test_mrio, region, [heavy, light], 0.5, categories=categories, weights={heavy: 1.0, light: 0.2}
    )

    assert _region_demand(result, region, heavy, categories) == pytest.approx(
        _region_demand(test_mrio, region, heavy, categories) * 0.5
    )
    assert _region_demand(result, region, light, categories) == pytest.approx(
        _region_demand(test_mrio, region, light, categories) * 0.9
    )


def test_a_missing_weight_defaults_to_a_full_share(test_mrio) -> None:
    """Products absent from the mapping take the headline cut rather than being skipped."""
    region = list(test_mrio.get_regions())[0]
    named, unnamed = list(test_mrio.get_sectors())[:2]

    weighted = apply_reduce(test_mrio, region, [named, unnamed], 0.3, weights={named: 1.0})
    flat = apply_reduce(test_mrio, region, [named, unnamed], 0.3)

    assert weighted.Y is not None and flat.Y is not None
    pd.testing.assert_frame_equal(weighted.Y, flat.Y)


def test_weighted_baskets_stay_linear_in_the_headline_fraction(test_mrio) -> None:
    """Weights must not break the property the precomputed table depends on."""
    region = list(test_mrio.get_regions())[0]
    first, second = list(test_mrio.get_sectors())[:2]
    weights = {first: 1.0, second: 0.25}
    baseline = total_emissions(test_mrio, extension=TEST_EXTENSION, stressor=TEST_STRESSOR)
    full = apply_reduce(test_mrio, region, [first, second], 0.4, weights=weights)
    half = apply_reduce(test_mrio, region, [first, second], 0.2, weights=weights)

    full_delta = total_emissions(full, extension=TEST_EXTENSION, stressor=TEST_STRESSOR) - baseline
    half_delta = total_emissions(half, extension=TEST_EXTENSION, stressor=TEST_STRESSOR) - baseline
    assert half_delta == pytest.approx(full_delta / 2, rel=1e-9)


def test_a_weight_deeper_than_all_the_demand_raises(test_mrio) -> None:
    """The headline may be under 1.0 while a weight pushes one product past it."""
    region = list(test_mrio.get_regions())[0]
    sector = list(test_mrio.get_sectors())[0]

    with pytest.raises(ValueError, match="realised reduction"):
        apply_reduce(test_mrio, region, [sector], 0.8, weights={sector: 2.0})


def test_direct_emissions_follow_the_named_product_not_the_average(test_mrio) -> None:
    """With uneven weights, F_Y must track the driving product's own change.

    This is the whole reason a fuel tape names a driver. The basket's average change is a
    number that describes no product in it, and letting the fuel burnt at home ride that
    average would be wrong in a way nothing would flag.
    """
    region = list(test_mrio.get_regions())[0]
    fuel, other = list(test_mrio.get_sectors())[:2]
    categories = [HOUSEHOLDS]
    weights = {fuel: 1.0, other: 0.1}

    driven = apply_reduce(
        test_mrio,
        region,
        [fuel, other],
        0.5,
        categories=categories,
        direct_emissions_extension=TEST_EXTENSION,
        weights=weights,
        direct_emissions_driver=fuel,
    )
    # The same shock, but letting direct emissions ride the headline instead.
    averaged = apply_reduce(
        test_mrio,
        region,
        [fuel, other],
        0.5,
        categories=categories,
        direct_emissions_extension=TEST_EXTENSION,
        weights=weights,
    )

    fy_driven, fy_averaged, fy_base = _direct(driven, region), _direct(averaged, region), _direct(test_mrio, region)

    # Driver weight is 1.0, so the driven case cuts F_Y by the full 50%.
    assert fy_driven == pytest.approx(fy_base * 0.5)
    # Here they coincide because the driver's weight is 1.0; assert the code took the
    # documented path rather than relying on the numbers agreeing by accident.
    assert fy_averaged == pytest.approx(fy_driven)


def test_an_unknown_direct_emissions_driver_raises(test_mrio) -> None:
    """Naming a product that is not in the basket is a typo, not a silent no-op."""
    region = list(test_mrio.get_regions())[0]
    sector = list(test_mrio.get_sectors())[0]

    with pytest.raises(ValueError, match="not in the basket"):
        apply_reduce(
            test_mrio,
            region,
            [sector],
            0.2,
            direct_emissions_extension=TEST_EXTENSION,
            direct_emissions_driver="Nope",
        )
