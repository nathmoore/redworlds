"""Tests for the spending-mix step (src/redworlds/engine/spending.py)."""

import pymrio
import pytest

from redworlds.engine.io_tables import GOVERNMENT, HOUSEHOLDS
from redworlds.engine.spending import shift_spending_mix, spending_factors


def _household_spend(mrio: pymrio.IOSystem, region: str, product: str) -> float:
    assert mrio.Y is not None
    return float(mrio.Y.loc[(slice(None), product), (region, HOUSEHOLDS)].sum())


def test_factors_follow_cap_et_al_equation_one() -> None:
    """Spending on a product grows by its elasticity times the change in income."""
    factors = spending_factors({"food": 0.5, "travel": 1.5}, income_change=0.4)

    assert factors == {"food": pytest.approx(1.2), "travel": pytest.approx(1.6)}


def test_a_factor_below_zero_is_an_error() -> None:
    """A fall in income large enough to make spending negative must not pass silently."""
    with pytest.raises(ValueError, match="below zero"):
        spending_factors({"travel": 3.0}, income_change=-0.5)


def test_the_household_total_is_unchanged_and_the_input_is_not_mutated(test_mrio: pymrio.IOSystem) -> None:
    """The step moves shares only: size belongs to the economy-size step."""
    assert test_mrio.Y is not None
    before = test_mrio.Y.copy()

    result = shift_spending_mix(test_mrio, "reg1", {"food": 0.5, "transport": 1.5}, income_change=0.5)

    assert result.Y is not None
    assert test_mrio.Y.equals(before)
    households = ("reg1", HOUSEHOLDS)
    assert float(result.Y[households].sum()) == pytest.approx(float(before[households].sum()))


def test_a_necessity_loses_share_and_a_luxury_gains_it(test_mrio: pymrio.IOSystem) -> None:
    """With rising income, spending moves from the low-elasticity product to the high one."""
    result = shift_spending_mix(test_mrio, "reg1", {"food": 0.5, "transport": 1.5}, income_change=0.5)

    assert _household_spend(result, "reg1", "food") < _household_spend(test_mrio, "reg1", "food")
    assert _household_spend(result, "reg1", "transport") > _household_spend(test_mrio, "reg1", "transport")


def test_the_ratio_between_two_products_is_the_ratio_of_their_factors(test_mrio: pymrio.IOSystem) -> None:
    """Rescaling to the old total leaves relative growth as Eq. 1 gives it."""
    result = shift_spending_mix(test_mrio, "reg1", {"food": 0.5, "transport": 1.5}, income_change=0.5)

    food_growth = _household_spend(result, "reg1", "food") / _household_spend(test_mrio, "reg1", "food")
    transport_growth = _household_spend(result, "reg1", "transport") / _household_spend(test_mrio, "reg1", "transport")
    assert transport_growth / food_growth == pytest.approx(1.75 / 1.25)


def test_elasticities_of_one_and_zero_income_change_both_do_nothing(test_mrio: pymrio.IOSystem) -> None:
    """A basket in which everything follows income, or an income that has not moved, is unchanged."""
    assert test_mrio.Y is not None
    all_one = dict.fromkeys(test_mrio.get_sectors(), 1.0)

    follows_income = shift_spending_mix(test_mrio, "reg1", all_one, income_change=0.8)
    no_change = shift_spending_mix(test_mrio, "reg1", {"food": 0.2}, income_change=0.0)

    assert follows_income.Y is not None and no_change.Y is not None
    assert follows_income.Y.to_numpy() == pytest.approx(test_mrio.Y.to_numpy())
    assert no_change.Y.to_numpy() == pytest.approx(test_mrio.Y.to_numpy())


def test_other_regions_and_other_final_demand_columns_are_left_alone(test_mrio: pymrio.IOSystem) -> None:
    """Only the named region's household column moves."""
    assert test_mrio.Y is not None
    result = shift_spending_mix(test_mrio, "reg1", {"food": 0.5}, income_change=0.5)

    assert result.Y is not None
    assert result.Y["reg2"].equals(test_mrio.Y["reg2"])
    assert result.Y[("reg1", GOVERNMENT)].equals(test_mrio.Y[("reg1", GOVERNMENT)])
