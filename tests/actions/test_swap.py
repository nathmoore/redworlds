"""Tests for the SWAP action (src/redworlds/actions/swap.py).

All tests use the ``test_mrio`` fixture from conftest.py — no EXIOBASE needed.

The physical-energy assertion is the important one: the service ratio is not a monetary
ratio. Source spend and replacement spend can differ sharply when their prices per TJ do.
"""

from typing import Any

import pymrio
import pytest

from redworlds.actions.swap import apply_swap
from redworlds.engine.io_tables import HOUSEHOLDS
from redworlds.engine.scoring import gdp_impact

TEST_EXTENSION = "emissions"
TEST_STRESSOR = ("emission_type1", "air")


def _account(mrio: pymrio.IOSystem) -> Any:
    return getattr(mrio, "emissions")  # noqa: B009 - pymrio attaches extensions dynamically


def test_swap_shifts_sector_share_and_closes_budget(test_mrio: pymrio.IOSystem) -> None:
    """Demand should shift from from_technology to to_technology proportionally."""
    assert test_mrio.Y is not None
    result = apply_swap(
        mrio=test_mrio,
        region="reg1",
        from_technology="food",
        replacement_technology="mining",
        pct_rollout=0.2,
        service_energy_ratio=1 / 3,
        energy_extension=TEST_EXTENSION,
        energy_stressor=TEST_STRESSOR,
    )
    assert result is not test_mrio, "apply_swap should return a new IO system"
    assert result.Y is not None
    before_food = test_mrio.Y.loc[(slice(None), "food"), ("reg1", HOUSEHOLDS)].sum()
    after_food = result.Y.loc[(slice(None), "food"), ("reg1", HOUSEHOLDS)].sum()
    # Re-spend can buy a little food back, but the direct 20% cut still dominates.
    assert after_food < before_food
    assert gdp_impact(test_mrio, result) == pytest.approx(0.0, abs=1e-9)


def test_swap_zero_is_identity(test_mrio: pymrio.IOSystem) -> None:
    result = apply_swap(test_mrio, "reg1", "food", "mining", 0.0, service_energy_ratio=1 / 3)
    assert result.Y is not None and test_mrio.Y is not None
    assert result.Y.equals(test_mrio.Y)


@pytest.mark.parametrize("fraction", [-0.1, 1.1])
def test_swap_rejects_invalid_rollout(test_mrio: pymrio.IOSystem, fraction: float) -> None:
    with pytest.raises(ValueError, match="pct_rollout"):
        apply_swap(test_mrio, "reg1", "food", "mining", fraction)


def test_swap_can_scale_direct_household_emissions(test_mrio: pymrio.IOSystem) -> None:
    result = apply_swap(
        test_mrio,
        "reg1",
        "manufactoring",
        "mining",
        0.2,
        service_energy_ratio=1 / 3,
        direct_emissions_extension="emissions",
        energy_extension=TEST_EXTENSION,
        energy_stressor=TEST_STRESSOR,
    )
    before = float(_account(test_mrio).F_Y.loc[("emission_type1", "air"), "reg1"].sum())
    after = float(_account(result).F_Y.loc[("emission_type1", "air"), "reg1"].sum())
    assert after == pytest.approx(0.8 * before)


def test_swap_applies_service_ratio_to_energy_not_spend(test_mrio: pymrio.IOSystem, monkeypatch) -> None:
    """One third means one third of removed TJ even when replacement money differs."""
    import redworlds.actions.swap as swap_module

    # Inspect the raw shift before rebound. Rebalancing has its own tests and otherwise buys
    # a little of both source and replacement back, obscuring the physical conversion.
    monkeypatch.setattr(swap_module, "rebalance_economy", lambda mrio, *_args, **_kwargs: mrio)
    assert test_mrio.Y is not None and test_mrio.x is not None
    account = _account(test_mrio)
    source = "food"
    replacement = "mining"
    columns = ("reg1", [HOUSEHOLDS])

    result = apply_swap(
        test_mrio,
        "reg1",
        source,
        replacement,
        0.2,
        service_energy_ratio=1 / 3,
        energy_extension=TEST_EXTENSION,
        energy_stressor=TEST_STRESSOR,
    )
    assert result.Y is not None

    prices = test_mrio.x["indout"] / account.F.loc[TEST_STRESSOR]
    removed = test_mrio.Y.loc[(slice(None), source), columns] - result.Y.loc[(slice(None), source), columns]
    added = result.Y.loc[(slice(None), replacement), columns] - test_mrio.Y.loc[(slice(None), replacement), columns]
    removed_active = removed.sum(axis=1) > 0.0
    added_active = added.sum(axis=1) > 0.0
    removed_rows = removed_active.index[removed_active]
    added_rows = added_active.index[added_active]
    removed_tj = float(removed.loc[removed_rows].div(prices.loc[removed_rows], axis="index").to_numpy().sum())
    added_tj = float(added.loc[added_rows].div(prices.loc[added_rows], axis="index").to_numpy().sum())
    assert added_tj == pytest.approx(removed_tj / 3)
    assert float(added.to_numpy().sum()) != pytest.approx(float(removed.to_numpy().sum()) / 3)


def test_swap_scales_only_the_named_direct_emissions_share(test_mrio: pymrio.IOSystem) -> None:
    result = apply_swap(
        test_mrio,
        "reg1",
        "manufactoring",
        "mining",
        0.5,
        service_energy_ratio=1 / 3,
        direct_emissions_extension=TEST_EXTENSION,
        direct_emissions_share=0.25,
        energy_extension=TEST_EXTENSION,
        energy_stressor=TEST_STRESSOR,
    )
    before = float(_account(test_mrio).F_Y.loc[TEST_STRESSOR, "reg1"].sum())
    after = float(_account(result).F_Y.loc[TEST_STRESSOR, "reg1"].sum())
    assert after == pytest.approx(before * (1 - 0.5 * 0.25))
