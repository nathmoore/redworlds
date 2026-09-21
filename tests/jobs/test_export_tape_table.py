"""Tests for the deterministic precomputed tape-table export."""

import json
from pathlib import Path
from typing import Any

import pymrio
import pytest

from redworlds.config import load_config
from redworlds.jobs.build_baseline import BASELINE_NAME
from redworlds.jobs.export_tape_table import (
    SCHEMA_PATH,
    _copies,
    _cover_reading,
    build_tape_table,
    write_tape_table,
)
from redworlds.jobs.tape_records import DEFAULT_OPTIONS_PATH, load_scenario_weights, load_tape_records


def _cached_baseline() -> pymrio.IOSystem:
    """Load the cached baseline, skipping if `just baseline` has not been run."""
    path = Path(load_config()["data"]["worlds_path"]) / BASELINE_NAME
    if not path.exists():
        pytest.skip(f"no cached baseline at {path} — run `just baseline`")
    return pymrio.load_all(path)


TEST_EXTENSION = "emissions"
TEST_STRESSOR = ("emission_type1", "air")


def _common(key: str, wing: str, status: str = "ready") -> dict[str, Any]:
    return {
        "key": key,
        "label": key,
        "wing": wing,
        "status": status,
        "region_id": 1,
        "scenario_category": "source",
        "matrix_target": ["Y"],
        "regional_ceiling": 1.0,
        "regional_ceiling_unit": "test units",
        "regional_ceiling_basis": "test",
        "beta_day_assumption": "held for a test" if status == "held" else "test",
        "build_years_reference": 0,
        "deployment_curve": f"{wing}_default",
        "cover_magnitude": {"things": 1},
    }


def test_build_table_solves_ready_y_side_tapes_and_keeps_held_record(test_mrio: pymrio.IOSystem) -> None:
    sectors = list(test_mrio.get_sectors())
    baskets = {"source": {sectors[0]: 1.0}, "replacement": {sectors[1]: 1.0}}
    reduce = {**_common("reduce", "reduce"), "max_reducible_fraction": 0.1}
    swap = {
        **_common("swap", "swap", "provisional"),
        "max_replaceable_fraction": 0.1,
        "replacement_category": "replacement",
        "service_energy_ratio": 1 / 3,
        "energy_extension": TEST_EXTENSION,
        "energy_stressor": TEST_STRESSOR,
    }
    build = {
        **_common("build", "build"),
        "build_years_reference": 5,
        "budget_musd_2026_purchaser": 100.0,
        "technology_sector": sectors[1],
        "cover_magnitude": {"things": 1, "twh_per_year": 0.001},
        "ceiling_cover_key": "things",
        "regional_ceiling": 10.0,
        "capex_split": {sectors[0]: 1.0},
        "fossil_sectors": [sectors[0]],
        "energy_extension": TEST_EXTENSION,
        "energy_stressor": TEST_STRESSOR,
    }
    held = _common("held", "swap", "held")

    table = build_tape_table(
        test_mrio,
        {"reduce": reduce, "swap": swap, "build": build, "held": held},
        baskets,
        baseline="test",
        provenance="test @ abc123",
        extension=TEST_EXTENSION,
        stressor=TEST_STRESSOR,
        co2_stressor=TEST_STRESSOR,
        region_names={1: "reg1"},
    )

    assert table["baseline"] == "test"
    assert table["tapes"]["held"]["status"] == "held"
    assert "annual_delta_operating_co2e_t" not in table["tapes"]["held"]
    assert table["tapes"]["reduce"]["annual_delta_operating_co2e_t"] < 0.0
    assert abs(table["tapes"]["swap"]["gdp_impact_full"]) < 1e-9
    assert table["tapes"]["swap"]["status"] == "provisional"
    assert table["tapes"]["swap"]["limitation"] == "test"
    assert set(table["tapes"]["build"]["deltas_by_deployment_co2e_t"]) == {"0.25", "0.5", "0.75", "1.0"}
    assert table["tapes"]["build"]["regional_ceiling_scale"] == 10.0


def test_write_table_is_byte_identical(tmp_path: Path) -> None:
    table = {"z": 1, "a": {"b": 2}}
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    write_tape_table(table, first)
    write_tape_table(table, second)
    assert first.read_bytes() == second.read_bytes()
    assert json.loads(first.read_text()) == table


def test_backfire_never_becomes_a_positive_copy_count() -> None:
    assert _copies(10e9) == 0
    assert _copies(-10e9) > 0


def test_committed_schema_is_valid_json() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert schema["$schema"].endswith("2020-12/schema")
    assert schema["properties"]["schema_version"]["const"] == 1


def test_cover_reading_states_which_deployment_it_was_solved_at() -> None:
    """Covers are calibrated against the cover figure, so it must be unambiguous.

    Two quantities have both been called "the brick reading": a BUILD tape is solved at its
    cover and a Y-side tape at its ceiling, and reporting both under ``cumulative_curve`` is
    how a calibration pass ends up comparing one against the other without noticing.
    """
    records = load_tape_records(DEFAULT_OPTIONS_PATH)

    build = _cover_reading(records["eca_nuclear"], -1.0e9, "cover")
    assert build["cumulative_at_cover_co2e_t"] == -1.0e9, "a BUILD tape is already at its cover"
    assert build["regional_ceiling_scale"] == pytest.approx(65.0)
    assert "solved at cover" in build["cover_basis"]

    buy_less = records["eca_buy_less"]
    y_side = _cover_reading(buy_less, -1.0e9, "ceiling")
    # Derived from the record, not pinned: covers move when they are recalibrated to the peg.
    scale = buy_less["regional_ceiling"] / buy_less["cover_magnitude"][buy_less["ceiling_cover_key"]]
    assert y_side["cumulative_at_cover_co2e_t"] == pytest.approx(-1.0e9 / scale), "scaled down to the cover"
    assert "solved at ceiling" in y_side["cover_basis"]


def test_a_non_linear_cover_is_reported_as_absent_not_guessed() -> None:
    """Extending a product's life removes N / (life + N) of demand, which is not linear in N.

    So the +1 year cover is not the +4 year ceiling divided by four, and scaling it would
    produce a confident wrong number. The export says so instead.
    """
    record = load_tape_records(DEFAULT_OPTIONS_PATH)["eca_extended_product_lifetimes"]

    reading = _cover_reading(record, -1.0e9, "ceiling")

    assert reading["cumulative_at_cover_co2e_t"] is None
    assert reading["bricks_at_cover"] is None
    assert "not linearly related" in reading["cover_basis"]


@pytest.mark.integration
def test_the_brick_is_the_peg() -> None:
    """A brick is what ten reactors deliver, so the constant must match nuclear's solve.

    The unit is declared rather than derived so it cannot move underfoot when the table is
    rebuilt — a brick that silently re-based itself would re-scale every other tape's copies
    with nothing failing. This is the trade for that: if nuclear's number genuinely changes,
    this breaks and ``BRICK_TONNES`` is updated deliberately.
    """
    world = _cached_baseline()
    table = build_tape_table(world, load_tape_records(), load_scenario_weights())

    assert table["tapes"]["eca_nuclear"]["bricks_at_cover"] == pytest.approx(1.0, abs=0.02)


@pytest.mark.integration
def test_every_solved_cover_lands_on_the_peg() -> None:
    """Covers are derived from the brick, so a solved tape should measure one.

    Excludes tapes that cannot be sized by scaling: a backfiring tape has no positive cover,
    a held tape has no solve, and the lifetimes cover is non-linear in years so its figure
    needs its own run.
    """
    world = _cached_baseline()
    table = build_tape_table(world, load_tape_records(), load_scenario_weights())

    for key, payload in table["tapes"].items():
        bricks = payload.get("bricks_at_cover")
        if bricks is None or bricks <= 0.0:
            continue
        assert bricks == pytest.approx(1.0, abs=0.1), f"{key} is {bricks:.2f} bricks at its cover"
