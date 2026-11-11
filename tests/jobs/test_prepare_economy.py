"""Tests for the economy data-preparation job (src/redworlds/jobs/prepare_economy.py)."""

import pandas as pd
import pytest

from redworlds.jobs.prepare_economy import economy_ledger, growth_factors, regional_totals

COUNTRY_REGIONS = {"AAA": "North", "BBB": "North", "CCC": "South"}


def _indicator(rows: list[tuple[str, int, float]]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["iso3", "year", "value"])


def _totals(indicator: pd.DataFrame) -> pd.DataFrame:
    return regional_totals(indicator, COUNTRY_REGIONS, first_year=2020, last_year=2021)


def test_countries_sum_into_regions_and_aggregates_are_dropped() -> None:
    """Countries add up by region; a code that is not a mapped country is ignored."""
    indicator = _indicator(
        [("AAA", 2020, 10.0), ("BBB", 2020, 5.0), ("WLD", 2020, 999.0), ("AAA", 2021, 11.0), ("BBB", 2021, 5.0)]
    )

    totals = _totals(indicator).set_index(["region", "year"])

    assert totals.loc[("North", 2020), "value"] == pytest.approx(15.0)
    assert totals.loc[("North", 2021), "value"] == pytest.approx(16.0)


def test_a_missing_year_is_carried_and_marks_the_row_provisional() -> None:
    """A country with no latest figure keeps its last one, and the ledger says so."""
    indicator = _indicator([("AAA", 2020, 10.0), ("AAA", 2021, 12.0), ("BBB", 2020, 4.0)])

    totals = _totals(indicator)
    ledger = economy_ledger({"GDP": totals}).set_index(["region", "year"])

    assert totals.set_index(["region", "year"]).loc[("North", 2021), "carried_share"] == pytest.approx(0.25)
    assert ledger.loc[("North", 2021), "status"] == "provisional"
    assert ledger.loc[("North", 2020), "status"] == "ready"


def test_growth_factors_are_the_ratio_to_the_base_year() -> None:
    """A region's factor is its value in the year over its value in the base year."""
    indicator = _indicator([("AAA", 2020, 10.0), ("AAA", 2021, 15.0), ("CCC", 2020, 8.0), ("CCC", 2021, 8.0)])
    ledger = economy_ledger({"GDP": _totals(indicator)})

    factors = growth_factors(ledger, 2021, base_year=2020)

    assert factors == {"North": pytest.approx(1.5), "South": pytest.approx(1.0)}


def test_growth_factors_for_a_year_not_in_the_ledger_is_an_error() -> None:
    """Asking for a year the ledger does not hold must not return an empty answer."""
    ledger = economy_ledger({"GDP": _totals(_indicator([("AAA", 2020, 10.0), ("AAA", 2021, 15.0)]))})

    with pytest.raises(ValueError, match="no GDP"):
        growth_factors(ledger, 2030, base_year=2020)
