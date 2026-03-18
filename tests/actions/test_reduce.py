"""Tests for the REDUCE action (src/redworlds/actions/reduce.py).

All tests use the ``test_mrio`` fixture from conftest.py — no EXIOBASE needed.

When implemented, these tests should verify:
- Final demand for the sector decreases by pct_reduction
- Total final demand decreases (NOT conserved — this is the post-growth behaviour)
- The returned IO system is a new object (original not mutated)
- Emissions decrease after a REDUCE action
- pct_reduction of 0.0 returns an unchanged IO system
- pct_reduction outside [0, 1] raises a clear error

TODO: implement — see GitHub issue #4
"""

import pytest

from redworlds.actions.reduce import apply_reduce


@pytest.mark.skip(reason="apply_reduce not yet implemented — see GitHub issue #4")
def test_reduce_decreases_final_demand(test_mrio):
    """Final demand for the target sector should decrease; economy should NOT rebalance."""
    result = apply_reduce(
        mrio=test_mrio,
        region="reg1",
        sector="residential_heating",
        pct_reduction=0.1,
    )
    assert result is not test_mrio, "apply_reduce should return a new IO system"


@pytest.mark.skip(reason="apply_reduce not yet implemented — see GitHub issue #4")
def test_reduce_does_not_rebalance(test_mrio):
    """Total final demand should be lower after REDUCE — post-growth, no rebalancing."""
    pass
