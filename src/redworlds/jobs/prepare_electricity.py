"""Turn Ember's country electricity data into the walk's regional generation targets.

A data-preparation job for the baseline walk (docs/design/baseline_walk.md). It reads the
raw Ember download, sums countries into the seven game regions and Ember's sources into
EXIOBASE electricity products, and writes two small committed files:

  - ``data/baseline/electricity_generation.csv`` — observed TWh by region, year and
    EXIOBASE product. These are the targets the electricity step is walked to.
  - ``data/baseline/electricity_observed.csv`` — observed total generation, emissions and
    emissions intensity by region and year. These are what the hindcast is checked against.

The raw download is large and stays out of git; the derived tables are small and are
committed with attribution, which Ember's CC BY 4.0 licence allows.

**Countries with no figure for a year.** Ember's latest year is published for about half of
all countries first. A country missing a year carries its most recent earlier figure forward,
for at most ``CARRY_FORWARD_YEARS`` years, and the share of each region's generation that
rests on a carried figure is written out beside it so it cannot pass unnoticed.

Run with ``just prepare-electricity``. Get the raw file as described in data/README.md.
"""

from pathlib import Path

import pandas as pd

from redworlds.engine.regions import load_region_concordance

REPO_ROOT = Path(__file__).parent.parent.parent.parent
EMBER_RAW = REPO_ROOT / "data" / "ember" / "release_generation_yearly_global.csv"
BASELINE_DATA = REPO_ROOT / "data" / "baseline"
COUNTRY_CONCORDANCE = REPO_ROOT / "data" / "concordances" / "country_to_exiobase.csv"
SOURCE_CONCORDANCE = REPO_ROOT / "data" / "concordances" / "ember_to_exiobase.csv"

FIRST_YEAR: int = 2011
LAST_YEAR: int = 2025
CARRY_FORWARD_YEARS: int = 2

SOURCE_NOTE: str = "Ember yearly electricity data"
LICENCE: str = "CC BY 4.0"


def load_source_concordance(path: Path = SOURCE_CONCORDANCE) -> pd.DataFrame:
    """Load the Ember source → EXIOBASE product table, indexed by Ember source."""
    return pd.read_csv(path, comment="#").set_index("ember_source")


def load_country_regions(
    path: Path = COUNTRY_CONCORDANCE,
    region_concordance: dict[str, str] | None = None,
) -> dict[str, str]:
    """Return {ISO3 country code: game region name}."""
    if region_concordance is None:
        region_concordance = load_region_concordance()
    countries = pd.read_csv(path, comment="#")
    return {
        str(iso3): region_concordance[str(block)]
        for iso3, block in zip(countries["iso3"], countries["exiobase_region"], strict=True)
    }


def carry_forward(values: pd.DataFrame, limit: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fill a country-by-year table forward along years; return it with a mask of filled cells."""
    filled = values.ffill(axis="columns", limit=limit)
    carried = values.isna() & filled.notna()
    return filled, carried


def regional_generation(
    ember: pd.DataFrame,
    country_regions: dict[str, str],
    sources: pd.DataFrame,
    first_year: int = FIRST_YEAR,
    last_year: int = LAST_YEAR,
    carry_forward_years: int = CARRY_FORWARD_YEARS,
) -> pd.DataFrame:
    """Sum Ember's country generation into game regions and EXIOBASE products.

    Args:
        ember: The raw Ember table (long format, one row per area, year and source).
        country_regions: {ISO3: game region}, from :func:`load_country_regions`.
        sources: The source concordance, from :func:`load_source_concordance`.
        first_year: First year to report.
        last_year: Last year to report.
        carry_forward_years: How many years a missing country figure may be carried.

    Returns:
        One row per region, year and EXIOBASE product: ``twh``, ``emissions_mtco2e`` and
        ``carried_twh`` (the part of ``twh`` resting on a carried-forward figure).
    """
    countries = ember[ember["ISO 3 code"].isin(country_regions) & ember["Electricity source"].isin(sources.index)]
    countries = countries[countries["Year"].between(first_year - carry_forward_years, last_year)]

    frames = []
    for column, name in (("Generation (TWh)", "twh"), ("Emissions (MtCO2e)", "emissions_mtco2e")):
        wide = countries.pivot_table(index=["ISO 3 code", "Electricity source"], columns="Year", values=column)
        wide = wide.reindex(columns=range(first_year - carry_forward_years, last_year + 1))
        filled, carried = carry_forward(wide, carry_forward_years)
        long = filled.stack().rename(name).to_frame()
        if name == "twh":
            long["carried_twh"] = filled.where(carried).stack().reindex(long.index).fillna(0.0)
        frames.append(long)
    table = pd.concat(frames, axis="columns").reset_index()
    table = table[table["Year"] >= first_year]

    table["region"] = table["ISO 3 code"].map(country_regions)
    table["product"] = table["Electricity source"].map(sources["exiobase_product"])
    summed = table.groupby(["region", "Year", "product"])[["twh", "emissions_mtco2e", "carried_twh"]].sum()
    # A region where no country reports a source still needs that product's row, at zero:
    # a missing row would leave the product at its base-year level instead of walking it out.
    every_row = pd.MultiIndex.from_product(
        [sorted(set(country_regions.values())), range(first_year, last_year + 1), list(sources["exiobase_product"])],
        names=["region", "year", "product"],
    )
    return summed.rename_axis(index={"Year": "year"}).reindex(every_row, fill_value=0.0).reset_index()


def generation_ledger(generation: pd.DataFrame, sources: pd.DataFrame) -> pd.DataFrame:
    """Shape regional generation as driver-ledger rows for the electricity step."""
    ipcc = sources.set_index("exiobase_product")["ipcc_variable"]
    return pd.DataFrame(
        {
            "step": "electricity",
            "region": generation["region"],
            "year": generation["year"],
            "variable": generation["product"],
            "value": generation["twh"].round(3),
            "unit": "TWh",
            "ipcc_variable": generation["product"].map(ipcc),
            "status": "ready",
            "source": SOURCE_NOTE,
            "licence": LICENCE,
        }
    )


def observed_totals(generation: pd.DataFrame) -> pd.DataFrame:
    """Return observed generation, emissions and intensity by region and year."""
    totals = generation.groupby(["region", "year"], as_index=False)[["twh", "emissions_mtco2e", "carried_twh"]].sum()
    totals["intensity_gco2e_per_kwh"] = (totals["emissions_mtco2e"] / totals["twh"] * 1_000.0).round(1)
    totals["carried_share"] = (totals["carried_twh"] / totals["twh"]).round(4)
    totals["twh"] = totals["twh"].round(3)
    totals["emissions_mtco2e"] = totals["emissions_mtco2e"].round(3)
    return totals.drop(columns="carried_twh")


def write_with_header(table: pd.DataFrame, path: Path, description: str) -> None:
    """Write a CSV whose first line is the column header, followed by ``#`` comment lines."""
    path.parent.mkdir(parents=True, exist_ok=True)
    comments = "\n".join(f"# {line}".rstrip() for line in description.splitlines())
    body = table.to_csv(index=False, lineterminator="\n")
    header, _, rows = body.partition("\n")
    path.write_text(f"{header}\n{comments}\n{rows}")


def main() -> None:
    """Rebuild the two committed electricity tables from the raw Ember download."""
    if not EMBER_RAW.exists():
        raise SystemExit(f"Ember download not found at {EMBER_RAW} — see data/README.md")
    ember = pd.read_csv(EMBER_RAW)
    sources = load_source_concordance()
    generation = regional_generation(ember, load_country_regions(), sources)

    write_with_header(
        generation_ledger(generation, sources),
        BASELINE_DATA / "electricity_generation.csv",
        "Observed electricity generation by game region, year and EXIOBASE product.\n"
        "The targets the electricity step of the baseline walk is walked to.\n"
        "Derived from Ember yearly electricity data (https://ember-energy.org), CC BY 4.0,\n"
        "by redworlds.jobs.prepare_electricity. Do not edit by hand; re-run the job.",
    )
    write_with_header(
        observed_totals(generation),
        BASELINE_DATA / "electricity_observed.csv",
        "Observed generation, power-sector emissions and emissions intensity by game region.\n"
        "What the electricity hindcast is checked against. Ember's emissions are lifecycle\n"
        "CO2e per technology, so they sit a little above direct combustion CO2.\n"
        "carried_share is the part of generation resting on a figure carried forward from an\n"
        "earlier year because the country had not yet been published for this one.\n"
        "Derived from Ember yearly electricity data (https://ember-energy.org), CC BY 4.0,\n"
        "by redworlds.jobs.prepare_electricity. Do not edit by hand; re-run the job.",
    )
    world = generation.groupby("year")["twh"].sum()
    print(f"Wrote {BASELINE_DATA}/electricity_generation.csv and electricity_observed.csv")
    first, last = world.loc[FIRST_YEAR], world.loc[LAST_YEAR]
    print(f"World generation: {first:,.0f} TWh in {FIRST_YEAR}, {last:,.0f} TWh in {LAST_YEAR}")


if __name__ == "__main__":
    main()
