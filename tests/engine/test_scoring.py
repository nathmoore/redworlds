"""Tests for scoring (src/redworlds/engine/scoring.py).

When implemented, these tests should verify:
- annual_delta of a system against itself is 0.0
- annual_delta is negative when the shocked system has lower total emissions
- cumulative_delta with a flat curve of 1.0 over 51 years equals 51 × the annual delta
- cumulative_delta with an all-zero curve is 0.0 and the jcurve is all zeros
- The jcurve covers 2050..2100 in five-year blocks (11 points)
- A BUILD-shaped curve (positive early, negative later) gives a jcurve that rises then falls

TODO: implement — see docs/backlog.md §Sequencing (GitHub issue pending)
"""

import pytest

from redworlds.engine.scoring import WINDOW_END, WINDOW_START, annual_delta, cumulative_delta  # noqa: F401


def test_window_is_fifty_years() -> None:
    """The scoring window is the game's 2050–2100 window."""
    assert (WINDOW_START, WINDOW_END) == (2050, 2100)


@pytest.mark.skip(reason="annual_delta not yet implemented — see docs/backlog.md")
def test_annual_delta_of_identical_systems_is_zero(test_mrio):
    pass


@pytest.mark.skip(reason="cumulative_delta not yet implemented — see docs/backlog.md")
def test_cumulative_delta_flat_curve():
    pass
