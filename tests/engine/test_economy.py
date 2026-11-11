"""Tests for the economy-size step of the baseline walk (src/redworlds/engine/economy.py)."""

import numpy as np
import pymrio
import pytest

from redworlds.engine.economy import scale_economies
from redworlds.engine.io_tables import recalculate_from_final_demand


def _final_demand(mrio: pymrio.IOSystem, region: str) -> np.ndarray:
    """Everything ``region``'s final consumers buy, from every producer."""
    assert mrio.Y is not None
    return mrio.Y.loc[:, (region, slice(None))].to_numpy()


def test_scaling_grows_only_the_named_regions_demand(test_mrio: pymrio.IOSystem) -> None:
    """A region's whole final demand moves by its factor; other regions' does not."""
    scaled = scale_economies(test_mrio, {"reg1": 1.5})

    np.testing.assert_allclose(_final_demand(scaled, "reg1"), _final_demand(test_mrio, "reg1") * 1.5)
    np.testing.assert_allclose(_final_demand(scaled, "reg2"), _final_demand(test_mrio, "reg2"))


def test_scaling_every_region_scales_world_output(test_mrio: pymrio.IOSystem) -> None:
    """With unchanged recipes, doubling all final demand doubles all output."""
    assert test_mrio.x is not None
    factors = dict.fromkeys(test_mrio.get_regions(), 2.0)

    solved = recalculate_from_final_demand(scale_economies(test_mrio, factors))

    assert solved.x is not None
    np.testing.assert_allclose(solved.x["indout"].to_numpy(), test_mrio.x["indout"].to_numpy() * 2.0)


def test_scaling_does_not_mutate_its_input(test_mrio: pymrio.IOSystem) -> None:
    """The original system's final demand is untouched."""
    before = _final_demand(test_mrio, "reg1").copy()

    scale_economies(test_mrio, {"reg1": 3.0})

    np.testing.assert_allclose(_final_demand(test_mrio, "reg1"), before)


def test_scaling_rejects_unknown_regions_and_negative_factors(test_mrio: pymrio.IOSystem) -> None:
    """A typo in a region name or a negative factor is an error, not a silent no-op."""
    with pytest.raises(ValueError, match="not in the table"):
        scale_economies(test_mrio, {"atlantis": 1.1})
    with pytest.raises(ValueError, match="non-negative"):
        scale_economies(test_mrio, {"reg1": -0.5})
