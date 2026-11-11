"""Tests for the electricity data-preparation job (src/redworlds/jobs/prepare_electricity.py).

The job's arithmetic is tested on a few hand-written rows in Ember's column layout, so no
download is needed. The committed concordances are checked for the properties the job
relies on.
"""

import pandas as pd
import pytest

from redworlds.jobs.prepare_electricity import (
    generation_ledger,
    load_country_regions,
    load_source_concordance,
    observed_totals,
    regional_generation,
)

SOURCES = pd.DataFrame(
    {
        "exiobase_product": ["Electricity by coal", "Electricity by wind"],
        "technology_class": ["fossil", "clean"],
        "ipcc_variable": ["Secondary Energy|Electricity|Coal", "Secondary Energy|Electricity|Wind"],
    },
    index=pd.Index(["Coal", "Wind"], name="ember_source"),
)
COUNTRY_REGIONS = {"AAA": "North", "BBB": "North", "CCC": "South"}


def _ember(rows: list[tuple[str, int, str, float, float]]) -> pd.DataFrame:
    """Build a miniature Ember table from (iso3, year, source, twh, emissions) rows."""
    return pd.DataFrame(
        rows, columns=["ISO 3 code", "Year", "Electricity source", "Generation (TWh)", "Emissions (MtCO2e)"]
    )


def _generation(ember: pd.DataFrame) -> pd.DataFrame:
    return regional_generation(ember, COUNTRY_REGIONS, SOURCES, first_year=2020, last_year=2021)


def test_countries_are_summed_into_their_region() -> None:
    """Two countries of one region add up, source by source."""
    ember = _ember(
        [
            ("AAA", 2020, "Coal", 10.0, 9.0),
            ("BBB", 2020, "Coal", 5.0, 4.5),
            ("AAA", 2021, "Coal", 10.0, 9.0),
            ("BBB", 2021, "Coal", 5.0, 4.5),
        ]
    )

    result = _generation(ember).set_index(["region", "year", "product"])

    assert result.loc[("North", 2020, "Electricity by coal"), "twh"] == pytest.approx(15.0)
    assert result.loc[("North", 2020, "Electricity by coal"), "emissions_mtco2e"] == pytest.approx(13.5)


def test_every_region_year_and_product_has_a_row() -> None:
    """A source nobody reports still gets a row, at zero, so the walk takes it to zero."""
    ember = _ember([("AAA", 2020, "Coal", 10.0, 9.0), ("AAA", 2021, "Coal", 10.0, 9.0)])

    result = _generation(ember)

    assert len(result) == 2 * 2 * 2  # regions x years x products
    wind = result[(result["region"] == "North") & (result["product"] == "Electricity by wind")]
    assert (wind["twh"] == 0.0).all()


def test_a_missing_year_is_carried_forward_and_counted() -> None:
    """A country with no figure for the latest year keeps its last one, flagged as carried."""
    ember = _ember(
        [
            ("AAA", 2020, "Coal", 10.0, 9.0),
            ("AAA", 2021, "Coal", 12.0, 10.0),
            ("BBB", 2020, "Coal", 4.0, 3.0),  # no 2021 figure for BBB
        ]
    )

    result = _generation(ember).set_index(["region", "year", "product"])
    row = result.loc[("North", 2021, "Electricity by coal")]

    assert row["twh"] == pytest.approx(16.0)
    assert row["carried_twh"] == pytest.approx(4.0)
    assert observed_totals(_generation(ember)).set_index(["region", "year"]).loc[
        ("North", 2021), "carried_share"
    ] == pytest.approx(0.25)


def test_observed_intensity_is_emissions_over_generation() -> None:
    """Mt CO2e over TWh, times a thousand, is grams per kWh."""
    ember = _ember([("CCC", 2020, "Coal", 100.0, 90.0), ("CCC", 2021, "Coal", 100.0, 90.0)])

    totals = observed_totals(_generation(ember)).set_index(["region", "year"])

    assert totals.loc[("South", 2020), "intensity_gco2e_per_kwh"] == pytest.approx(900.0)


def test_ledger_rows_carry_source_licence_and_ipcc_name() -> None:
    """Each ledger row says where its number came from and which IPCC variable it matches."""
    ember = _ember([("AAA", 2020, "Coal", 10.0, 9.0), ("AAA", 2021, "Coal", 10.0, 9.0)])

    ledger = generation_ledger(_generation(ember), SOURCES)

    coal = ledger[ledger["variable"] == "Electricity by coal"].iloc[0]
    assert coal["step"] == "electricity"
    assert coal["unit"] == "TWh"
    assert coal["ipcc_variable"] == "Secondary Energy|Electricity|Coal"
    assert coal["licence"] == "CC BY 4.0"


def test_committed_source_concordance_is_one_to_one() -> None:
    """Nine Ember sources, nine distinct EXIOBASE products, each classed clean or fossil."""
    sources = load_source_concordance()

    assert len(sources) == 9
    assert sources["exiobase_product"].is_unique
    assert set(sources["technology_class"]) == {"clean", "fossil"}


def test_committed_country_concordance_reaches_every_game_region() -> None:
    """Every country lands in one of the seven game regions, and all seven are reached."""
    regions = load_country_regions()

    assert len(regions) > 200
    assert len(set(regions.values())) == 7
