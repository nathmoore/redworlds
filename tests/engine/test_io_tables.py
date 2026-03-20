"""Tests for IO table operations (src/redworlds/engine/io_tables.py).

All tests use the ``test_mrio`` fixture from conftest.py — no EXIOBASE needed.

When implemented, these tests should verify:
- scale_final_demand with factor=1.0 returns an identical IO system
- scale_final_demand with factor=0.0 zeros out the target sector demand
- scale_final_demand does not mutate the input IO system
- shift_sector_share conserves total demand (from + to unchanged in sum)
- get_sector_emissions returns a non-negative float for a known sector

TODO: implement — see GitHub issues #11, #12, #13
"""

import pytest

from redworlds.engine.io_tables import (  # noqa: F401
    get_sector_emissions,
    scale_final_demand,
    shift_sector_share,
)


@pytest.mark.skip(reason="scale_final_demand not yet implemented — see GitHub issue #11")
def test_scale_final_demand_identity(test_mrio):
    """Scaling by 1.0 should return an IO system equivalent to the input."""
    result = scale_final_demand(test_mrio, region="reg1", sector="food", factor=1.0)
    assert result is not test_mrio, "should return a new object"


@pytest.mark.skip(reason="shift_sector_share not yet implemented — see GitHub issue #12")
def test_shift_sector_share_conserves_total(test_mrio):
    """Total demand across from_sector + to_sector should be unchanged after a shift."""
    pass


@pytest.mark.skip(reason="get_sector_emissions not yet implemented — see GitHub issue #13")
def test_get_sector_emissions_non_negative(test_mrio):
    """Emissions for any sector in the test IO world should be >= 0."""
    pass
