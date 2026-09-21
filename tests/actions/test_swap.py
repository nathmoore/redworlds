"""Tests for the SWAP action (src/redworlds/actions/swap.py).

All tests use the ``test_mrio`` fixture from conftest.py — no EXIOBASE needed.

When implemented, these tests should verify:
- ``from_technology`` sector demand decreases by pct_rollout
- ``to_technology`` sector demand increases by an equivalent amount
- Total final demand is conserved (economy rebalanced)
- The returned IO system is a new object (original not mutated)
- pct_rollout of 0.0 returns an unchanged IO system
- pct_rollout outside [0, 1] raises a clear error

TODO: implement — see GitHub issue #7
"""

from typing import Any

import pymrio
import pytest

from redworlds.actions.swap import apply_swap
from redworlds.engine.io_tables import HOUSEHOLDS
from redworlds.engine.scoring import gdp_impact


def _account(mrio: pymrio.IOSystem) -> Any:
    return getattr(mrio, "emissions")  # noqa: B009 - pymrio attaches extensions dynamically


def test_swap_shifts_sector_share_and_closes_budget(test_mrio: pymrio.IOSystem) -> None:
    """Demand should shift from from_technology to to_technology proportionally."""
    assert test_mrio.Y is not None
    result = apply_swap(
        mrio=test_mrio,
        region="reg1",
        from_technology="food",
        to_technology="mining",
        pct_rollout=0.2,
        replacement_ratio=1 / 3,
    )
    assert result is not test_mrio, "apply_swap should return a new IO system"
    assert result.Y is not None
    before_food = test_mrio.Y.loc[(slice(None), "food"), ("reg1", HOUSEHOLDS)].sum()
    after_food = result.Y.loc[(slice(None), "food"), ("reg1", HOUSEHOLDS)].sum()
    # Re-spend can buy a little food back, but the direct 20% cut still dominates.
    assert after_food < before_food
    assert gdp_impact(test_mrio, result) == pytest.approx(0.0, abs=1e-9)


def test_swap_zero_is_identity(test_mrio: pymrio.IOSystem) -> None:
    result = apply_swap(test_mrio, "reg1", "food", "mining", 0.0, replacement_ratio=1 / 3)
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
        replacement_ratio=1 / 3,
        direct_emissions_extension="emissions",
    )
    before = float(_account(test_mrio).F_Y.loc[("emission_type1", "air"), "reg1"].sum())
    after = float(_account(result).F_Y.loc[("emission_type1", "air"), "reg1"].sum())
    assert after == pytest.approx(0.8 * before)
