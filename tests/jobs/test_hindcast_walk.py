"""Tests for the walk hindcast job (src/redworlds/jobs/hindcast_walk.py).

The run needs the cached EXIOBASE baseline, so only the handling of observed data is
tested here.
"""

import pandas as pd
import pytest

from redworlds.jobs.hindcast_walk import observed_co2_gt

RAW = pd.DataFrame(
    {
        "country": ["Aland", "Bland", "Cland", "World", "Aland"],
        "iso_code": ["AAA", "BBB", "CCC", None, "AAA"],
        "year": [2020, 2020, 2020, 2020, 2021],
        "co2": [1000.0, 500.0, 250.0, 2000.0, None],
    }
)
COUNTRY_REGIONS = {"AAA": "North", "BBB": "North", "CCC": "South"}


def test_observed_co2_sums_countries_into_regions_in_gigatonnes() -> None:
    """Megatonnes by country become gigatonnes by region."""
    observed = observed_co2_gt(RAW, COUNTRY_REGIONS).set_index(["region", "year"])["co2_gt"]

    assert observed[("North", 2020)] == pytest.approx(1.5)
    assert observed[("South", 2020)] == pytest.approx(0.25)


def test_observed_world_total_is_the_published_world_row() -> None:
    """The world figure is the dataset's own, which includes international transport."""
    observed = observed_co2_gt(RAW, COUNTRY_REGIONS).set_index(["region", "year"])["co2_gt"]

    assert observed[("World", 2020)] == pytest.approx(2.0)


def test_a_year_with_no_figures_is_absent_rather_than_zero() -> None:
    """A missing observation must not read as zero emissions."""
    observed = observed_co2_gt(RAW, COUNTRY_REGIONS).set_index(["region", "year"])["co2_gt"]

    assert ("North", 2021) not in observed.index
