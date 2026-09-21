"""Tests for the tape runner (src/redworlds/jobs/run_tapes.py).

Unit tests build their own records against the pymrio test world, so they check the
record-to-engine translation rather than the committed numbers. The integration tests run
the three real REDUCE tapes against the cached baseline.

The load-bearing test here is ``test_annual_delta_is_linear_in_the_fraction``. The whole
precomputed-table design (contract §4.4) rests on solving each tape once at full deployment
and letting the game multiply by the realised outcome fraction. If that were only
approximately true, every score the game computes would be wrong by an amount nobody could
see, so it is asserted rather than assumed.
"""

from pathlib import Path
from typing import Any

import pymrio
import pytest

from redworlds.config import load_config
from redworlds.engine.regions import load_region_concordance
from redworlds.engine.scoring import WINDOW_END, WINDOW_START
from redworlds.jobs.build_baseline import BASELINE_NAME, build_baseline
from redworlds.jobs.run_tapes import FLAT_CURVE, run_ready_reduce_tapes, run_reduce_tape
from redworlds.jobs.tape_records import load_scenario_weights, load_tape_records

BETA_DAY_REDUCE_TAPES = ("eca_buy_less", "eca_extended_product_lifetimes", "eca_remote_work_commuters")

CONCORDANCE_PATH = Path(__file__).parents[1] / "fixtures" / "test_world_regions.csv"

# pymrio's test world carries an `emissions` extension with two-level row labels, where
# EXIOBASE carries `impacts` with a single characterised GHG row.
TEST_EXTENSION = "emissions"
TEST_STRESSOR = ("emission_type1", "air")


@pytest.fixture
def game_world(test_mrio: pymrio.IOSystem) -> pymrio.IOSystem:
    """The test world aggregated to game regions, so a record's region_id resolves for real.

    Records name their region by id and the real concordance turns that into a label, so a
    world labelled reg1..reg6 would test the translation with the translation removed.
    """
    return build_baseline(test_mrio, capital_use=None, concordance=load_region_concordance(CONCORDANCE_PATH))


@pytest.fixture
def test_baskets(game_world: pymrio.IOSystem) -> dict[str, dict[str, float]]:
    """A two-product basket drawn from the test world's own sectors, flat weights."""
    sectors = list(game_world.get_sectors())
    return {"test_basket": {sectors[0]: 1.0, sectors[1]: 1.0}}


def _record(**overrides: Any) -> dict[str, Any]:
    """A complete REDUCE record pointed at the test world."""
    return {
        "key": "test_tape",
        "wing": "reduce",
        "status": "ready",
        "region_id": 1,
        "scenario_category": "test_basket",
        "max_reducible_fraction": 0.2,
        **overrides,
    }


def test_solves_a_reduce_tape_at_its_ceiling(game_world, test_baskets) -> None:
    """The fraction applied is the record's ceiling, and the tape abates."""
    result = run_reduce_tape(game_world, _record(), test_baskets, extension=TEST_EXTENSION, stressor=TEST_STRESSOR)

    assert result.key == "test_tape"
    assert result.region == "USA and Canada"
    assert result.pct_reduction == 0.2
    assert result.products == 2
    assert result.annual_delta < 0, "cutting demand must not raise emissions"
    assert result.gdp_impact < 0, "REDUCE books a contraction under rule RE2"


def test_annual_delta_is_linear_in_the_fraction(game_world, test_baskets) -> None:
    """One solve at full deployment must be enough — the contract §4.4 assumption.

    The game multiplies a tape's full-deployment delta by the realised outcome fraction.
    That is only sound if the delta is exactly proportional to the fraction, so halving the
    fraction must halve the delta to floating-point precision, not merely approximately.
    """
    full = run_reduce_tape(
        game_world, _record(max_reducible_fraction=0.4), test_baskets, extension=TEST_EXTENSION, stressor=TEST_STRESSOR
    )
    half = run_reduce_tape(
        game_world, _record(max_reducible_fraction=0.2), test_baskets, extension=TEST_EXTENSION, stressor=TEST_STRESSOR
    )

    assert half.annual_delta == pytest.approx(full.annual_delta / 2, rel=1e-9)
    assert half.gdp_impact == pytest.approx(full.gdp_impact / 2, rel=1e-9)
    assert half.cumulative_full_flat == pytest.approx(full.cumulative_full_flat / 2, rel=1e-9)


def test_linearity_holds_with_the_direct_emissions_correction(game_world, test_baskets) -> None:
    """The F_Y correction scales a column, so it must not break linearity either."""
    kwargs = {"direct_emissions_extension": "emissions"}
    full = run_reduce_tape(
        game_world,
        _record(max_reducible_fraction=0.4, **kwargs),
        test_baskets,
        extension=TEST_EXTENSION,
        stressor=TEST_STRESSOR,
    )
    half = run_reduce_tape(
        game_world,
        _record(max_reducible_fraction=0.2, **kwargs),
        test_baskets,
        extension=TEST_EXTENSION,
        stressor=TEST_STRESSOR,
    )

    assert half.annual_delta == pytest.approx(full.annual_delta / 2, rel=1e-9)
    # And the correction must actually change the answer, or the test above proves nothing.
    plain = run_reduce_tape(
        game_world, _record(max_reducible_fraction=0.4), test_baskets, extension=TEST_EXTENSION, stressor=TEST_STRESSOR
    )
    assert full.annual_delta != pytest.approx(plain.annual_delta)


def test_final_demand_categories_are_honoured(game_world, test_baskets) -> None:
    """A tape can narrow the columns it cuts; remote work cuts households only."""
    households = ["Final consumption expenditure by households"]
    narrow = run_reduce_tape(
        game_world,
        _record(final_demand_categories=households),
        test_baskets,
        extension=TEST_EXTENSION,
        stressor=TEST_STRESSOR,
    )
    wide = run_reduce_tape(game_world, _record(), test_baskets, extension=TEST_EXTENSION, stressor=TEST_STRESSOR)

    assert abs(narrow.gdp_impact) < abs(wide.gdp_impact), "cutting fewer columns must remove less spend"


def test_build_record_is_refused(game_world, test_baskets) -> None:
    """A BUILD tape needs machinery this function does not have; failing loudly is right."""
    with pytest.raises(ValueError, match="is a build tape"):
        run_reduce_tape(
            game_world, _record(wing="build"), test_baskets, extension=TEST_EXTENSION, stressor=TEST_STRESSOR
        )


def test_pending_tapes_are_skipped(game_world, test_baskets) -> None:
    """Sprint 2 solves the ready records and leaves the other six alone."""
    records = {
        "ready_one": _record(key="ready_one"),
        "not_yet": _record(key="not_yet", status="pending"),
        "a_build": _record(key="a_build", wing="build", status="pending"),
    }

    results = run_ready_reduce_tapes(
        game_world, records, test_baskets, extension=TEST_EXTENSION, stressor=TEST_STRESSOR
    )

    assert set(results) == {"ready_one"}


def test_flat_curve_covers_the_whole_window() -> None:
    """One multiplier per year, or cumulative_delta refuses it."""
    assert len(FLAT_CURVE) == WINDOW_END - WINDOW_START + 1
    assert set(FLAT_CURVE) == {1.0}


def test_jcurve_runs_the_window_in_five_year_blocks(game_world, test_baskets) -> None:
    """The game charts these points, so the first and last years must be the window's."""
    result = run_reduce_tape(game_world, _record(), test_baskets, extension=TEST_EXTENSION, stressor=TEST_STRESSOR)

    assert result.jcurve[0]["year"] == WINDOW_START
    assert result.jcurve[-1]["year"] == WINDOW_END
    assert all(point["value"] == pytest.approx(result.annual_delta) for point in result.jcurve)


def _cached_baseline() -> pymrio.IOSystem:
    """Load the cached baseline, skipping the test if `just baseline` has not been run."""
    path = Path(load_config()["data"]["worlds_path"]) / BASELINE_NAME
    if not path.exists():
        pytest.skip(f"no cached baseline at {path} — run `just baseline`")
    return pymrio.load_all(path)


@pytest.mark.integration
def test_the_three_beta_day_tapes_all_solve() -> None:
    """T3's done condition: three real tapes, three plausible numbers."""
    results = run_ready_reduce_tapes(_cached_baseline(), load_tape_records(), load_scenario_weights())

    assert set(results) == set(BETA_DAY_REDUCE_TAPES)
    for key, result in results.items():
        assert result.region == "Europe and Central Asia", key
        assert result.annual_delta < 0, f"{key} must abate"
        assert result.gdp_impact < 0, f"{key} must book a contraction"
        # A brick is 1 Gt. A tape worth less than a tenth of one, or more than the region's
        # entire footprint over the window, would mean the basket or the ceiling is wrong.
        bricks = -result.cumulative_full_flat / 1e12
        assert 0.1 < bricks < 500, f"{key} is {bricks:.2f} bricks, which is not a game tape"


@pytest.mark.integration
def test_remote_work_is_far_more_carbon_intense_than_buying_less() -> None:
    """A basket of nothing but burnt fuel must behave like one.

    This is the clearest evidence the F_Y correction and the tight basket are both working:
    per euro removed, commuting fuel should be several times basket A, which is mostly
    manufactured goods whose emissions sit in supply chains abroad.
    """
    results = run_ready_reduce_tapes(_cached_baseline(), load_tape_records(), load_scenario_weights())

    def intensity(key: str) -> float:
        result = results[key]
        return result.annual_delta / result.gdp_impact

    assert intensity("eca_remote_work_commuters") > 3 * intensity("eca_buy_less")
