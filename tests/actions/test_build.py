"""Tests for the BUILD action (src/redworlds/actions/build.py).

All tests use the ``test_mrio`` fixture from conftest.py — no EXIOBASE needed.

When implemented, these tests should verify:
- CapEx is correctly spread over the build period (budget / build_years per year)
- The energy mix is only updated after the build period completes
- The returned IO system is a new object (original not mutated)
- Economy is rebalanced after the build (total output conserved)
- Invalid region or technology raises a clear error

TODO: implement — see GitHub issue #6
"""

import pytest

from redworlds.actions.build import apply_build


@pytest.mark.skip(reason="apply_build not yet implemented — see GitHub issue #6")
def test_build_spreads_capex_linearly(test_mrio):
    """CapEx should be evenly distributed across the build period."""
    result = apply_build(
        mrio=test_mrio,
        region="reg1",
        technology="offshore_wind",
        budget=1_000_000,
        build_years=5,
        current_year=1,
    )
    assert result is not test_mrio, "apply_build should return a new IO system"
