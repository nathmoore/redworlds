"""Tests for the spending data-preparation job (src/redworlds/jobs/prepare_spending.py).

The supplement and the EXIOBASE download are not needed: each function is tested on a
small table of the same shape.
"""

import pandas as pd
import pytest

from redworlds.engine.io_tables import HOUSEHOLDS
from redworlds.jobs.prepare_spending import (
    BUDGET_SHARE,
    CATEGORIES,
    ELASTICITY,
    category_spending,
    household_spending_by_product,
    product_elasticities,
    regional_elasticities,
    spending_ledger,
    tidy_elasticities,
    tidy_product_concordance,
)

FOOD, CLOTHING, FURNITURE = CATEGORIES[3], CATEGORIES[4], CATEGORIES[6]


def _concordance_sheet() -> pd.DataFrame:
    """Three products in the supplement's layout: a grid with blanks, and two empty trailing rows."""
    grid = pd.DataFrame(None, index=["Bread", "Shirts", "Leather", None, None], columns=range(15), dtype=object)
    grid.loc["Bread", 3] = 1
    grid.loc["Shirts", 4] = 1
    grid.loc["Leather", 4] = 0.5
    grid.loc["Leather", 6] = 0.5
    return grid


def test_the_concordance_becomes_one_row_per_product_and_category() -> None:
    """Blank cells and empty rows are dropped; a split product gets two rows."""
    concordance = tidy_product_concordance(_concordance_sheet())

    pairs = dict(
        zip(
            zip(concordance["exiobase_product"], concordance["consumption_category"], strict=True),
            concordance["share"],
            strict=True,
        )
    )
    assert pairs == {
        ("Bread", FOOD): 1.0,
        ("Shirts", CLOTHING): 1.0,
        ("Leather", CLOTHING): 0.5,
        ("Leather", FURNITURE): 0.5,
    }


def test_a_product_whose_shares_do_not_sum_to_one_is_an_error() -> None:
    sheet = _concordance_sheet()
    sheet.loc["Leather", 6] = 0.3

    with pytest.raises(ValueError, match="do not sum to one"):
        tidy_product_concordance(sheet)


def test_the_elasticity_sheet_must_have_fifteen_categories() -> None:
    with pytest.raises(ValueError, match="category rows"):
        tidy_elasticities(pd.DataFrame({"AA": [1.0, 0.5]}, index=["one", "two"]))


def test_household_spending_adds_imports_to_domestic_purchases() -> None:
    """What a region's households buy of a product is summed over every producing region."""
    index = pd.MultiIndex.from_product([["AA", "BB"], ["Bread", "Shirts"]])
    columns = pd.MultiIndex.from_product([["AA", "BB"], [HOUSEHOLDS, "Other"]])
    final_demand = pd.DataFrame(1.0, index=index, columns=columns)
    final_demand.loc[("BB", "Bread"), ("AA", HOUSEHOLDS)] = 4.0

    spending = household_spending_by_product(final_demand)

    assert spending.loc["Bread", "AA"] == pytest.approx(5.0)
    assert spending.loc["Shirts", "BB"] == pytest.approx(2.0)


def test_a_split_product_is_divided_between_its_categories() -> None:
    concordance = tidy_product_concordance(_concordance_sheet())
    by_product = pd.DataFrame({"AA": [10.0, 6.0, 4.0]}, index=["Bread", "Shirts", "Leather"])

    spending = category_spending(by_product, concordance)

    assert spending.loc[FOOD, "AA"] == pytest.approx(10.0)
    assert spending.loc[CLOTHING, "AA"] == pytest.approx(8.0)
    assert spending.loc[FURNITURE, "AA"] == pytest.approx(2.0)


def test_a_product_with_no_category_is_an_error() -> None:
    concordance = tidy_product_concordance(_concordance_sheet())

    with pytest.raises(ValueError, match="no consumption category"):
        category_spending(pd.DataFrame({"AA": [1.0]}, index=["Unmapped"]), concordance)


def test_a_game_region_takes_the_spending_weighted_average_of_its_members() -> None:
    """The member that spends more on a category counts for more in that category's elasticity."""
    elasticities = pd.DataFrame({"AA": [0.5, 1.0], "BB": [1.0, 2.0], "CC": [0.8, 1.2]}, index=[FOOD, CLOTHING])
    spending = pd.DataFrame({"AA": [30.0, 10.0], "BB": [10.0, 10.0], "CC": [5.0, 5.0]}, index=[FOOD, CLOTHING])
    regions = {"AA": "North", "BB": "North", "CC": "South"}

    regional = regional_elasticities(elasticities, spending, regions).set_index(["region", "category"])

    assert regional.loc[("North", FOOD), "elasticity"] == pytest.approx((0.5 * 30 + 1.0 * 10) / 40)
    assert regional.loc[("North", CLOTHING), "elasticity"] == pytest.approx(1.5)
    assert regional.loc[("South", FOOD), "elasticity"] == pytest.approx(0.8)
    assert regional.loc[("North", FOOD), "budget_share"] == pytest.approx(40 / 60)


def test_products_read_their_elasticity_through_the_concordance() -> None:
    """A split product takes the share-weighted average of its two categories."""
    regional = pd.DataFrame(
        {
            "region": ["North"] * 3,
            "category": [FOOD, CLOTHING, FURNITURE],
            "elasticity": [0.6, 1.0, 1.4],
            "budget_share": [0.5, 0.3, 0.2],
        }
    )
    ledger = spending_ledger(regional)
    concordance = tidy_product_concordance(_concordance_sheet())

    by_product = product_elasticities(ledger, concordance)

    assert set(ledger["variable"]) == {ELASTICITY, BUDGET_SHARE}
    assert by_product["North"] == {
        "Bread": pytest.approx(0.6),
        "Shirts": pytest.approx(1.0),
        "Leather": pytest.approx(1.2),
    }


def test_the_committed_tables_cover_every_region_and_keep_spending_shares_adding_up() -> None:
    """Engel aggregation: budget share times elasticity, summed over categories, is close to one."""
    ledger = pd.read_csv("data/baseline/income_elasticities.csv", comment="#")
    table = ledger.pivot_table(index=["region", "category"], columns="variable", values="value")

    marginal_total = (table[ELASTICITY] * table[BUDGET_SHARE]).groupby(level="region").sum()

    assert len(marginal_total) == 7
    assert (table[ELASTICITY] > 0.0).all()
    assert marginal_total.to_numpy() == pytest.approx(1.0, abs=0.05)
