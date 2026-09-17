"""Tests for scoring (src/redworlds/engine/scoring.py).

Everything here runs on pymrio's built-in test world, so no EXIOBASE download is needed.
That world's satellite account is ``emissions`` with two-level stressor rows, so the
tests pass the extension and stressor explicitly rather than relying on the
EXIOBASE-specific defaults.
"""

import pytest

from redworlds.engine.io_tables import recalculate_from_final_demand, scale_final_demand
from redworlds.engine.scoring import (
    WINDOW_END,
    WINDOW_START,
    annual_delta,
    cumulative_delta,
    gdp_impact,
)

TEST_EXTENSION = "emissions"
TEST_STRESSOR = ("emission_type1", "air")
WINDOW_LENGTH = WINDOW_END - WINDOW_START + 1


@pytest.fixture
def halved_food_mrio(test_mrio):
    """The test world with reg1's final demand for food halved, recalculated."""
    cut = scale_final_demand(test_mrio, "reg1", "food", 0.5)
    return recalculate_from_final_demand(cut)


def test_window_is_fifty_years() -> None:
    """The scoring window is the game's 2050–2100 window."""
    assert (WINDOW_START, WINDOW_END) == (2050, 2100)


def test_annual_delta_of_identical_systems_is_zero(test_mrio) -> None:
    """A world compared with itself has moved no carbon."""
    assert annual_delta(test_mrio, test_mrio, TEST_EXTENSION, TEST_STRESSOR) == 0.0


def test_annual_delta_is_negative_when_demand_is_cut(test_mrio, halved_food_mrio) -> None:
    """Cutting final demand abates, so the delta is negative."""
    delta = annual_delta(test_mrio, halved_food_mrio, TEST_EXTENSION, TEST_STRESSOR)
    assert delta < 0.0


def test_annual_delta_is_antisymmetric(test_mrio, halved_food_mrio) -> None:
    """Swapping baseline and shocked flips the sign: the delta is a plain difference."""
    abated = annual_delta(test_mrio, halved_food_mrio, TEST_EXTENSION, TEST_STRESSOR)
    reversed_delta = annual_delta(halved_food_mrio, test_mrio, TEST_EXTENSION, TEST_STRESSOR)
    assert reversed_delta == pytest.approx(-abated)


def test_cumulative_delta_flat_curve(test_mrio, halved_food_mrio) -> None:
    """A fully deployed intervention repeats its annual delta in every year of the window."""
    delta = annual_delta(test_mrio, halved_food_mrio, TEST_EXTENSION, TEST_STRESSOR)
    result = cumulative_delta(delta, [1.0] * WINDOW_LENGTH)

    assert result["co2_delta_cumulative"] == pytest.approx(WINDOW_LENGTH * delta)
    assert [point["year"] for point in result["jcurve"]] == list(range(2050, 2101, 5))
    assert len(result["jcurve"]) == 11
    assert all(point["value"] == pytest.approx(delta) for point in result["jcurve"])


def test_cumulative_delta_zero_curve_scores_nothing() -> None:
    """A tape that never deploys scores zero, whatever its full-deployment delta."""
    result = cumulative_delta(-1.0e9, [0.0] * WINDOW_LENGTH)

    assert result["co2_delta_cumulative"] == 0.0
    assert all(point["value"] == 0.0 for point in result["jcurve"])


def test_cumulative_delta_rejects_wrong_curve_length() -> None:
    """A curve that does not cover the window is a caller bug, not something to pad."""
    with pytest.raises(ValueError, match="one multiplier per year"):
        cumulative_delta(-1.0e9, [1.0] * 50)


def test_cumulative_delta_build_is_two_phases_summed() -> None:
    """A BUILD tape emits while it is built, then abates: the summed J-curve starts above zero.

    Construction and operation are separate shocks with their own annual deltas, so BUILD
    scores each through its own 0-to-1 curve and adds the results.
    """
    construction_years = 10
    building = [1.0] * construction_years + [0.0] * (WINDOW_LENGTH - construction_years)
    operating = [0.0] * construction_years + [1.0] * (WINDOW_LENGTH - construction_years)
    hump = cumulative_delta(+2.0e8, building)  # capex emits
    displacement = cumulative_delta(-1.0e9, operating)  # new plant abates

    total = hump["co2_delta_cumulative"] + displacement["co2_delta_cumulative"]
    jcurve = [
        {"year": h["year"], "value": h["value"] + d["value"]}
        for h, d in zip(hump["jcurve"], displacement["jcurve"], strict=True)
    ]
    assert (jcurve[0]["year"], jcurve[-1]["year"]) == (2050, 2100)
    assert jcurve[0]["value"] > 0.0
    assert jcurve[-1]["value"] < 0.0
    assert total == pytest.approx(10 * 2.0e8 - 41 * 1.0e9)


def test_gdp_impact_of_identical_systems_is_zero(test_mrio) -> None:
    """No shock, no booked contraction."""
    assert gdp_impact(test_mrio, test_mrio) == 0.0


def test_gdp_impact_books_the_spend_that_left_the_model(test_mrio, halved_food_mrio) -> None:
    """Under RE2 the removed final demand is exactly the GDP reduction booked."""
    # Halving reg1's food demand removes half of that block of the original Y.
    food_bought_by_reg1 = test_mrio.Y.loc[(slice(None), "food"), ("reg1", slice(None))].to_numpy().sum()

    impact = gdp_impact(test_mrio, halved_food_mrio)

    assert impact < 0.0
    assert impact == pytest.approx(-0.5 * float(food_bought_by_reg1))
