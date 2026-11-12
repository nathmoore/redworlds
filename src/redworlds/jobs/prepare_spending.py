"""Turn published income elasticities into the walk's spending-mix inputs.

A data-preparation job for the baseline walk (docs/design/baseline_walk.md). It reads the
supplement to Bjelle et al. 2021, who estimate how household spending on fifteen consumption
categories responds to income in each of EXIOBASE's 49 regions, and writes two small
committed files:

  - ``data/concordances/exiobase_to_consumption_category.csv`` — which of the fifteen
    categories each of EXIOBASE's 200 products belongs to.
  - ``data/baseline/income_elasticities.csv`` — one income elasticity per game region and
    category, as driver-ledger rows, with the 2011 budget share beside it.

**What an income elasticity is.** The percentage by which spending on a category rises when
income rises by one per cent. Below one is a necessity (food); above one is a luxury
(eating out, travel). The published figures are for 49 regions; a game region's figure is
the average of its members', weighted by what each member's households spent on that
category in the 2011 table. That weighting is exact if every member's income grows by the
same percentage, and an approximation otherwise.

Two things use the result: the spending-mix step of the walk (``engine/spending.py``), and
the weighting of re-spent money in SWAP and BUILD (``engine/balancing.py``).

The supplement and the EXIOBASE download stay out of git. The derived tables are committed
with attribution, which the paper's CC BY 4.0 licence allows.

Run with ``just prepare-spending``. Get the raw files as described in data/README.md.

Source: Bjelle, Wiebe, Többen, Tisserant, Ivanova, Vita & Wood (2021), Energy Economics 95,
105114, https://doi.org/10.1016/j.eneco.2021.105114 — supplementary workbooks
``SI_regression_data.xlsx`` (sheet ``eps_income``) and ``SI_concordances.xlsx`` (sheet
``Products``).
"""

from pathlib import Path

import openpyxl
import pandas as pd

from redworlds.config import load_config
from redworlds.engine.io_tables import HOUSEHOLDS
from redworlds.engine.regions import load_region_concordance
from redworlds.jobs.prepare_electricity import BASELINE_DATA, REPO_ROOT, write_with_header

BJELLE_RAW = REPO_ROOT / "data" / "bjelle2021"
PRODUCT_CONCORDANCE = REPO_ROOT / "data" / "concordances" / "exiobase_to_consumption_category.csv"
ELASTICITY_LEDGER = BASELINE_DATA / "income_elasticities.csv"

# The fifteen consumption categories, in the order both workbooks list them. The two
# workbooks spell several names differently, so categories are matched by position and
# given these names (the spelling of SI_regression_data.xlsx).
CATEGORIES: tuple[str, ...] = (
    "Vegetables, fruit, nuts, rice and crops",
    "Fish, Meat and dairy",
    "Tobacco and beverages",
    "Food nec",
    "Clothing",
    "Housing, real estate, water, gas, electricity and other fuels",
    "Furniture, Household goods and services",
    "Health, education, insurance and social security",
    "Transport services and fuels nec",
    "Railway, air and other transportation services",
    "Communication services",
    "Recreation and culture",
    "Restaurants and hotels",
    "Motor Vehicles",
    "Miscellaneous goods and services",
)
BASE_YEAR: int = 2011
SOURCE: str = "Bjelle et al. 2021 (doi:10.1016/j.eneco.2021.105114), supplement"
LICENCE: str = "CC BY 4.0"
ELASTICITY: str = "Income elasticity"
BUDGET_SHARE: str = "Budget share"


def read_sheet(path: Path, sheet_name: str) -> pd.DataFrame:
    """Read one worksheet as a table, with its first row as columns and first column as index.

    openpyxl is used directly because the version pymrio pins is older than the one
    ``pandas.read_excel`` accepts.
    """
    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    header, *rows = workbook[sheet_name].iter_rows(values_only=True)
    table = pd.DataFrame([row[1:] for row in rows], index=[row[0] for row in rows], columns=list(header[1:]))
    return table.loc[:, table.columns.notna()]


def tidy_product_concordance(sheet: pd.DataFrame) -> pd.DataFrame:
    """Reshape the supplement's product-by-category grid into one row per pairing.

    Args:
        sheet: The ``Products`` sheet read with its first column as the index: one row per
            EXIOBASE product, one column per category, a share where the product belongs
            to the category and blank or zero elsewhere.

    Returns:
        Rows of ``exiobase_product``, ``consumption_category`` and ``share``. A product's
        shares sum to one; nearly every product has a single row.

    Raises:
        ValueError: If the sheet does not have fifteen category columns, or a product's
            shares do not sum to one.
    """
    grid = sheet[sheet.index.notna()]
    if grid.shape[1] != len(CATEGORIES):
        raise ValueError(f"expected {len(CATEGORIES)} category columns; found {grid.shape[1]}")
    grid = grid.set_axis(list(CATEGORIES), axis="columns").fillna(0.0).astype(float)
    totals = grid.sum(axis="columns")
    unbalanced = totals[(totals - 1.0).abs() > 1e-9]
    if len(unbalanced):
        raise ValueError(f"category shares do not sum to one for: {list(unbalanced.index)}")
    long = grid.rename_axis(index="exiobase_product", columns="consumption_category").stack().rename("share")
    return long[long > 0.0].reset_index()


def tidy_elasticities(sheet: pd.DataFrame) -> pd.DataFrame:
    """Return the supplement's elasticity grid as categories (rows) by EXIOBASE regions (columns)."""
    grid = sheet[sheet.index.notna()].dropna(axis="columns", how="all").astype(float)
    if grid.shape[0] != len(CATEGORIES):
        raise ValueError(f"expected {len(CATEGORIES)} category rows; found {grid.shape[0]}")
    return grid.set_axis(list(CATEGORIES), axis="index")


def household_spending_by_product(final_demand: pd.DataFrame, category: str = HOUSEHOLDS) -> pd.DataFrame:
    """Sum what each region's households buy of each product, wherever it was made.

    Args:
        final_demand: A ``Y`` table: rows (producing region, product), columns (consuming
            region, final-demand category).
        category: The final-demand category to read; households by default.

    Returns:
        Products (rows) by consuming regions (columns), in the table's money unit.
    """
    households = final_demand.xs(category, axis="columns", level=1)
    return households.groupby(level=1, sort=False).sum()


def category_spending(spending_by_product: pd.DataFrame, concordance: pd.DataFrame) -> pd.DataFrame:
    """Add product spending up into consumption categories, splitting products that sit in two."""
    shares = concordance.pivot(index="exiobase_product", columns="consumption_category", values="share").fillna(0.0)
    missing = sorted(set(spending_by_product.index) - set(shares.index))
    if missing:
        raise ValueError(f"products with no consumption category: {missing}")
    return pd.DataFrame(shares.reindex(spending_by_product.index).T @ spending_by_product.clip(lower=0.0))


def regional_elasticities(
    elasticities: pd.DataFrame,
    spending: pd.DataFrame,
    region_concordance: dict[str, str],
) -> pd.DataFrame:
    """Average member regions' elasticities into game regions, weighted by category spending.

    Args:
        elasticities: Categories by EXIOBASE regions, from :func:`tidy_elasticities`.
        spending: Categories by EXIOBASE regions, from :func:`category_spending`.
        region_concordance: {EXIOBASE region: game region}.

    Returns:
        One row per game region and category: ``elasticity`` and ``budget_share`` (the
        category's share of the game region's household spending).
    """
    members = [region for region in elasticities.columns if region in spending.columns]
    game_region = pd.Series({region: region_concordance[region] for region in members})
    weights = spending[members]
    weighted = (elasticities[members] * weights).T.groupby(game_region).sum().T
    totals = weights.T.groupby(game_region).sum().T
    result = pd.DataFrame(
        {
            "elasticity": (weighted / totals).stack(),
            "budget_share": (totals / totals.sum(axis="index")).stack(),
        }
    )
    return result.rename_axis(index=["category", "region"]).reset_index()


def spending_ledger(regional: pd.DataFrame) -> pd.DataFrame:
    """Shape regional elasticities and budget shares as driver-ledger rows."""
    frames = []
    for variable, column, source in (
        (ELASTICITY, "elasticity", f"{SOURCE}; averaged over member regions by 2011 household spending"),
        (
            BUDGET_SHARE,
            "budget_share",
            "EXIOBASE 3.8.2 household final demand, grouped by the same supplement's concordance",
        ),
    ):
        frames.append(
            pd.DataFrame(
                {
                    "step": "spending",
                    "region": regional["region"],
                    "year": BASE_YEAR,
                    "category": regional["category"],
                    "variable": variable,
                    "value": regional[column].round(4),
                    "unit": "dimensionless",
                    "ipcc_variable": "",
                    "status": "ready",
                    "source": source,
                    "licence": LICENCE if variable == ELASTICITY else "CC BY-SA 4.0",
                }
            )
        )
    ledger = pd.concat(frames, ignore_index=True)
    return ledger.sort_values(["variable", "region", "category"], kind="stable").reset_index(drop=True)


def product_elasticities(
    ledger: pd.DataFrame | None = None,
    concordance: pd.DataFrame | None = None,
) -> dict[str, dict[str, float]]:
    """Return {game region: {EXIOBASE product: income elasticity}} from the committed tables.

    A product that sits in two categories takes the share-weighted average of their
    elasticities. This is the form the spending step and the re-spend weighting take.

    Args:
        ledger: The elasticity ledger; read from ``data/baseline/`` when omitted.
        concordance: The product concordance; read from ``data/concordances/`` when omitted.
    """
    ledger = pd.read_csv(ELASTICITY_LEDGER, comment="#") if ledger is None else ledger
    concordance = pd.read_csv(PRODUCT_CONCORDANCE, comment="#") if concordance is None else concordance
    rows = ledger[ledger["variable"] == ELASTICITY]
    by_category = rows.pivot(index="category", columns="region", values="value")
    paired = concordance.join(by_category, on="consumption_category")
    regions = list(by_category.columns)
    weighted = paired[regions].mul(paired["share"], axis="index").groupby(paired["exiobase_product"]).sum()
    return {region: weighted[region].to_dict() for region in regions}


def main() -> None:
    """Rebuild the product concordance and the elasticity ledger from the raw downloads."""
    regression_path = BJELLE_RAW / "SI_regression_data.xlsx"
    concordance_path = BJELLE_RAW / "SI_concordances.xlsx"
    final_demand_path = Path(load_config()["data"]["exiobase_path"]) / "IOT_2011_pxp" / "Y.txt"
    for path in (regression_path, concordance_path, final_demand_path):
        if not path.exists():
            raise SystemExit(f"raw file not found at {path} — see data/README.md")

    concordance = tidy_product_concordance(read_sheet(concordance_path, "Products"))
    elasticities = tidy_elasticities(read_sheet(regression_path, "eps_income"))
    final_demand = pd.read_csv(final_demand_path, sep="\t", index_col=[0, 1], header=[0, 1])
    spending = category_spending(household_spending_by_product(final_demand), concordance)
    regional = regional_elasticities(elasticities, spending, load_region_concordance())

    write_with_header(
        concordance,
        PRODUCT_CONCORDANCE,
        "Maps EXIOBASE 3.8.2 (pxp) products to the fifteen household consumption categories of\n"
        "Bjelle et al. 2021 (https://doi.org/10.1016/j.eneco.2021.105114). share is the part of\n"
        "the product's household spending counted in the category; one product is split.\n"
        "Adapted from the paper's supplement (SI_concordances.xlsx), CC BY 4.0, by\n"
        "redworlds.jobs.prepare_spending. Do not edit by hand; re-run the job.",
    )
    write_with_header(
        spending_ledger(regional),
        ELASTICITY_LEDGER,
        "Income elasticity of household spending, and 2011 budget share, by game region and\n"
        "consumption category: the inputs to the spending-mix step of the baseline walk and to\n"
        "the weighting of re-spent money in SWAP and BUILD. An elasticity of 0.6 means spending\n"
        "on the category rises 0.6% when income rises 1%.\n"
        "Elasticities adapted from Bjelle et al. 2021 (https://doi.org/10.1016/j.eneco.2021.105114),\n"
        "supplement SI_regression_data.xlsx, CC BY 4.0: the published figures for EXIOBASE's 49\n"
        "regions, averaged into game regions by redworlds.jobs.prepare_spending.\n"
        "Do not edit by hand; re-run the job.",
    )
    print(f"Wrote {PRODUCT_CONCORDANCE} and {ELASTICITY_LEDGER}")
    table = regional.pivot(index="category", columns="region", values="elasticity").reindex(list(CATEGORIES))
    pd.set_option("display.width", 250)
    print(table.round(2).to_string())


if __name__ == "__main__":
    main()
