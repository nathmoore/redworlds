"""Tests for the walk hindcast job (src/redworlds/jobs/hindcast_walk.py).

The run needs the cached EXIOBASE baseline, so the full run is not tested here: only the
handling of observed data and the helpers that feed the spending step.
"""

import pandas as pd
import pymrio
import pytest

from redworlds.jobs.hindcast_walk import income_changes, observed_co2_gt, shift_all_spending

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


def test_income_change_is_growth_in_gdp_per_person() -> None:
    """GDP up by half with population up by a quarter is income per head up by a fifth."""
    economy = pd.DataFrame(
        {
            "region": ["North"] * 4,
            "year": [2011, 2025, 2011, 2025],
            "variable": ["GDP", "GDP", "Population", "Population"],
            "value": [100.0, 150.0, 10.0, 12.5],
        }
    )

    assert income_changes(economy, 2025) == {"North": pytest.approx(0.2)}


def test_spending_is_shifted_only_where_elasticities_exist(test_mrio: pymrio.IOSystem) -> None:
    """A region with an income change but no elasticities is left as it was."""
    assert test_mrio.Y is not None
    result = shift_all_spending(test_mrio, {"reg1": {"food": 0.5}}, {"reg1": 0.5, "reg2": 0.5})

    assert result.Y is not None
    assert not result.Y["reg1"].equals(test_mrio.Y["reg1"])
    assert result.Y["reg2"].equals(test_mrio.Y["reg2"])
