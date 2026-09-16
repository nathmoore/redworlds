"""Tests for the baseline job (src/redworlds/jobs/build_baseline.py).

When implemented, these tests should verify, on the pymrio test world with
capital_use_path=None:
- The returned system is calculated (has L and D_cba) and is a new object
- Monetary matrices are scaled by the currency conversion factor
- Stepping to target_year applies the growth multipliers (compare against apply_growth)
- The integration test builds the real 2050 baseline and checks it has 7 regions

TODO: implement — see docs/backlog.md §Sequencing (GitHub issue pending)
"""

import pytest

from redworlds.jobs.build_baseline import build_baseline


@pytest.mark.skip(reason="build_baseline not yet implemented — see docs/backlog.md")
def test_build_baseline_returns_calculated_system(test_mrio):
    result = build_baseline(test_mrio, capital_use_path=None, target_year=2050)
    assert result is not test_mrio
