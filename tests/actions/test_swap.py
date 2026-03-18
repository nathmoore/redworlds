"""Tests for the SWAP action (src/redworlds/actions/swap.py).

All tests use the ``test_mrio`` fixture from conftest.py — no EXIOBASE needed.

When implemented, these tests should verify:
- ``from_technology`` sector demand decreases by pct_rollout
- ``to_technology`` sector demand increases by an equivalent amount
- Total final demand is conserved (economy rebalanced)
- The returned IO system is a new object (original not mutated)
- pct_rollout of 0.0 returns an unchanged IO system
- pct_rollout outside [0, 1] raises a clear error

TODO: implement — see GitHub issue #3
"""

import pytest

from redworlds.actions.swap import apply_swap


@pytest.mark.skip(reason="apply_swap not yet implemented — see GitHub issue #3")
def test_swap_shifts_sector_share(test_mrio):
    """Demand should shift from from_technology to to_technology proportionally."""
    result = apply_swap(
        mrio=test_mrio,
        region="reg1",
        from_technology="gas_heating",
        to_technology="heat_pumps",
        pct_rollout=0.2,
    )
    assert result is not test_mrio, "apply_swap should return a new IO system"
