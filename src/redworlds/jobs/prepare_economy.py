"""Turn World Bank GDP and population into the walk's regional economy-size inputs.

A data-preparation job for the baseline walk (docs/design/baseline_walk.md). It reads two
raw World Development Indicators downloads, sums countries into the seven game regions and
writes ``data/baseline/economy.csv``: real GDP and population by region and year, as driver
ledger rows. The economy-size step scales each region's final demand by the ratio of its
GDP in the target year to its GDP in the base year.

The raw downloads stay out of git; the derived table is committed with attribution, which
the World Bank's CC BY 4.0 terms for these two series allow.

**Countries with no figure for a year** carry their most recent earlier figure forward, for
at most ``CARRY_FORWARD_YEARS`` years. A region-year where more than
``PROVISIONAL_CARRIED_SHARE`` of the total rests on carried figures is marked
``provisional`` instead of ``ready``.

**Taiwan** has no World Bank series. It is absent from both the numerator and the
denominator of Mainland East Asia's growth ratio, which therefore describes the rest of
the region.

Run with ``just prepare-economy``. Get the raw files as described in data/README.md.
"""

import json
from pathlib import Path

import pandas as pd

from redworlds.jobs.prepare_electricity import (
    BASELINE_DATA,
    REPO_ROOT,
    carry_forward,
    load_country_regions,
    write_with_header,
)

WORLD_BANK_RAW = REPO_ROOT / "data" / "worldbank"

FIRST_YEAR: int = 2011
LAST_YEAR: int = 2025
CARRY_FORWARD_YEARS: int = 2
PROVISIONAL_CARRIED_SHARE: float = 0.05

# {ledger variable: (World Bank indicator code, unit, matching IPCC scenario variable)}
INDICATORS: dict[str, tuple[str, str, str]] = {
    "GDP": ("NY.GDP.MKTP.KD", "constant 2015 US$", "GDP|MER"),
    "Population": ("SP.POP.TOTL", "people", "Population"),
}
LICENCE: str = "CC BY 4.0"


def load_indicator(path: Path) -> pd.DataFrame:
    """Read one World Bank API download as rows of ``iso3``, ``year`` and ``value``."""
    _, records = json.loads(path.read_text())
    rows = [
        {"iso3": record["countryiso3code"], "year": int(record["date"]), "value": record["value"]}
        for record in records
        if record["countryiso3code"] and record["value"] is not None
    ]
    return pd.DataFrame(rows)


def regional_totals(
    indicator: pd.DataFrame,
    country_regions: dict[str, str],
    first_year: int = FIRST_YEAR,
    last_year: int = LAST_YEAR,
    carry_forward_years: int = CARRY_FORWARD_YEARS,
) -> pd.DataFrame:
    """Sum one country-level indicator into game regions.

    Countries are matched by ISO3 code, which also drops the World Bank's regional and
    income-group aggregates from the download.

    Returns:
        One row per region and year: ``value`` and ``carried_share`` (the part of ``value``
        resting on a figure carried forward from an earlier year).
    """
    countries = indicator[indicator["iso3"].isin(country_regions)]
    wide = countries.pivot_table(index="iso3", columns="year", values="value")
    wide = wide.reindex(columns=range(first_year - carry_forward_years, last_year + 1))
    filled, carried = carry_forward(wide, carry_forward_years)

    region_of = filled.index.map(country_regions)
    totals = filled.groupby(region_of).sum()
    carried_totals = filled.where(carried, 0.0).groupby(region_of).sum()

    long = totals.stack().rename("value").to_frame()
    long["carried_share"] = (carried_totals / totals).stack().reindex(long.index)
    long = long.rename_axis(index=["region", "year"]).reset_index()
    return long[long["year"] >= first_year].reset_index(drop=True)


def economy_ledger(totals_by_variable: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Shape regional GDP and population as driver-ledger rows for the economy-size step."""
    frames = []
    for variable, totals in totals_by_variable.items():
        code, unit, ipcc_variable = INDICATORS[variable]
        provisional = totals["carried_share"] > PROVISIONAL_CARRIED_SHARE
        frames.append(
            pd.DataFrame(
                {
                    "step": "economy",
                    "region": totals["region"],
                    "year": totals["year"],
                    "variable": variable,
                    "value": totals["value"].round(0),
                    "unit": unit,
                    "ipcc_variable": ipcc_variable,
                    "status": provisional.map({True: "provisional", False: "ready"}),
                    "source": f"World Bank World Development Indicators ({code})",
                    "licence": LICENCE,
                }
            )
        )
    return pd.concat(frames, ignore_index=True)


def growth_factors(
    ledger: pd.DataFrame, year: int, base_year: int = FIRST_YEAR, variable: str = "GDP"
) -> dict[str, float]:
    """Return {region: value in ``year`` over value in ``base_year``} for one ledger variable."""
    rows = ledger[ledger["variable"] == variable].pivot(index="region", columns="year", values="value")
    if year not in rows.columns or base_year not in rows.columns:
        raise ValueError(f"the ledger has no {variable} for {base_year} and {year}")
    return (rows[year] / rows[base_year]).to_dict()


def main() -> None:
    """Rebuild ``data/baseline/economy.csv`` from the raw World Bank downloads."""
    country_regions = load_country_regions()
    totals = {}
    for variable, (code, _, _) in INDICATORS.items():
        path = WORLD_BANK_RAW / f"{code}.json"
        if not path.exists():
            raise SystemExit(f"World Bank download not found at {path} — see data/README.md")
        totals[variable] = regional_totals(load_indicator(path), country_regions)
    ledger = economy_ledger(totals)

    write_with_header(
        ledger,
        BASELINE_DATA / "economy.csv",
        "Real GDP and population by game region and year: the inputs to the economy-size step\n"
        "of the baseline walk. status is provisional where more than 5% of a figure rests on\n"
        "country values carried forward from an earlier year. Taiwan has no World Bank series.\n"
        "Derived from the World Bank's World Development Indicators\n"
        "(https://data.worldbank.org), CC BY 4.0, by redworlds.jobs.prepare_economy.\n"
        "Do not edit by hand; re-run the job.",
    )
    factors = growth_factors(ledger, LAST_YEAR)
    print(f"Wrote {BASELINE_DATA}/economy.csv")
    print(f"Real GDP, {LAST_YEAR} over {FIRST_YEAR}:")
    for region, factor in sorted(factors.items()):
        print(f"  {region}: {factor:.2f}")


if __name__ == "__main__":
    main()
