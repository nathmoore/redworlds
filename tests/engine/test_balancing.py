"""Tests for economic balancing (src/redworlds/engine/balancing.py).

All tests use the ``test_mrio`` fixture from conftest.py — no EXIOBASE needed.

When implemented, these tests should verify:
- rebalance_economy returns a new IO system (original not mutated)
- Total output is conserved across the economy after rebalancing
- Rebalancing a system with no changes returns an effectively identical system
- The changed sector's new value is preserved after rebalancing

TODO: implement — see GitHub issue #10
"""

import pytest

from redworlds.engine.balancing import rebalance_economy


@pytest.mark.skip(reason="rebalance_economy not yet implemented — see GitHub issue #10")
def test_rebalance_conserves_total_output(test_mrio):
    """Total economic output should be conserved (or within tolerance) after rebalancing."""
    result = rebalance_economy(test_mrio, changed_region="reg1", changed_sector="food")
    assert result is not test_mrio, "should return a new object"
