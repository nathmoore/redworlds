"""Tests for the Smart Grid coefficient shock."""

import numpy as np
import pymrio
import pytest

from redworlds.actions.grid import apply_grid_efficiency


def test_grid_efficiency_reduces_inputs_without_changing_y(test_mrio: pymrio.IOSystem) -> None:
    assert test_mrio.A is not None and test_mrio.Y is not None
    result = apply_grid_efficiency(
        test_mrio,
        "reg1",
        generation_sectors=("food",),
        delivery_sectors=("mining",),
    )
    assert result.A is not None and result.Y is not None
    assert (
        result.A.loc[(slice(None), "food"), ("reg1", "mining")].sum().sum()
        < test_mrio.A.loc[(slice(None), "food"), ("reg1", "mining")].sum().sum()
    )
    assert result.A.loc[(slice(None), ["food", "mining"]), ("reg1", "manufactoring")].sum().sum() < (
        test_mrio.A.loc[(slice(None), ["food", "mining"]), ("reg1", "manufactoring")].sum().sum()
    )
    assert result.Y.equals(test_mrio.Y)


def test_grid_efficiency_does_not_move_generation_shares(test_mrio: pymrio.IOSystem) -> None:
    assert test_mrio.A is not None
    result = apply_grid_efficiency(
        test_mrio,
        "reg1",
        generation_sectors=("food", "mining"),
        delivery_sectors=("transport",),
        demand_response_fraction=0.0,
    )
    assert result.A is not None
    before = test_mrio.A.loc[(slice(None), ["food", "mining"]), ("reg1", "transport")]
    after = result.A.loc[(slice(None), ["food", "mining"]), ("reg1", "transport")]
    ratios = after.to_numpy() / before.to_numpy()
    assert np.nanmax(ratios) == pytest.approx(np.nanmin(ratios))


@pytest.mark.parametrize("fraction", [-0.1, 1.1])
def test_grid_efficiency_rejects_invalid_deployment(test_mrio: pymrio.IOSystem, fraction: float) -> None:
    with pytest.raises(ValueError, match="deployment_fraction"):
        apply_grid_efficiency(
            test_mrio,
            "reg1",
            deployment_fraction=fraction,
            generation_sectors=("food",),
            delivery_sectors=("mining",),
        )
