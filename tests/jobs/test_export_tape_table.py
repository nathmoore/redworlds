"""Tests for the deterministic precomputed tape-table export."""

import json
from pathlib import Path
from typing import Any

import pymrio

from redworlds.jobs.export_tape_table import SCHEMA_PATH, _copies, build_tape_table, write_tape_table

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
