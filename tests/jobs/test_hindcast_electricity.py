"""Tests for the electricity hindcast job (src/redworlds/jobs/hindcast_electricity.py).

The run itself needs the cached EXIOBASE baseline, so it is not exercised here. These tests
cover the piece that turns ledger rows into the shares the step is walked to.
"""

import pandas as pd
import pytest

from redworlds.jobs.hindcast_electricity import target_shares

GENERATION = pd.DataFrame(
    {
        "region": ["North", "North", "South"],
        "year": [2020, 2020, 2020],
        "variable": ["Electricity by coal", "Electricity by wind", "Electricity by coal"],
        "value": [30.0, 10.0, 5.0],
    }
)


def test_target_shares_are_each_products_part_of_the_regions_generation() -> None:
    """Shares are TWh over the region's total for that year, and sum to one."""
    shares = target_shares(GENERATION, "North", 2020)

    assert shares == {"Electricity by coal": pytest.approx(0.75), "Electricity by wind": pytest.approx(0.25)}


def test_target_shares_for_an_unknown_year_is_an_error() -> None:
    """A year with no rows must not quietly become an empty mix."""
    with pytest.raises(ValueError, match="no generation targets"):
        target_shares(GENERATION, "North", 1999)
