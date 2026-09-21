"""Solve the committed tapes and write the deterministic table consumed by Red Carbon.

Eight records are executable. The smart-grid record is exported as ``status: held`` because
its mechanism gate has not been settled; no plausible-looking zero is invented for it.
BUILD operating shocks are sampled at four deployment fractions because changing ``A`` and
re-inverting the Leontief matrix is non-linear.
"""

import json
import math
import subprocess
from datetime import date
from pathlib import Path
from typing import Any

import pymrio

from redworlds.config import load_config
from redworlds.engine.intensity import TARGET_YEAR, intensity_scalar
from redworlds.engine.io_tables import CO2_STRESSOR, GHG_STRESSOR
from redworlds.jobs.build_baseline import BASELINE_NAME
from redworlds.jobs.run_tapes import (
    BuildTapeResult,
    ReduceTapeResult,
    SwapTapeResult,
    run_build_tape,
    run_reduce_tape,
    run_swap_tape,
)
from redworlds.jobs.tape_records import load_scenario_weights, load_tape_records, validate_baskets

_REPO_ROOT = Path(__file__).parents[3]
DEFAULT_EXPORT_DIR = _REPO_ROOT / "data" / "exports"
SCHEMA_PATH = _REPO_ROOT / "data" / "tech_choices" / "tape_table.schema.json"
BRICK_TONNES: float = 1e9
KG_TO_TONNES: float = 1e-3


def _provenance() -> str:
    """Return a stable source identifier without making export depend on Git being present."""
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=_REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        commit = "unknown"
    return f"jobs/export_tape_table.py @ {commit}"


def _common(record: dict[str, Any], provenance: str) -> dict[str, Any]:
    return {
        "status": record["status"],
        "region_id": record["region_id"],
        "wing": record["wing"],
        "build_years_reference": record.get("build_years_reference", 0),
        "deployment_curve": record["deployment_curve"],
        "cover_magnitude": record["cover_magnitude"],
        "regional_ceiling": record["regional_ceiling"],
        "regional_ceiling_unit": record["regional_ceiling_unit"],
        "provenance": provenance,
    }


def _copies(cumulative_curve_t: float) -> int:
    """Whole 2050-intensity bricks delivered by the full regional ceiling."""
    return max(0, math.floor(abs(cumulative_curve_t) * intensity_scalar(TARGET_YEAR) / BRICK_TONNES))


def _y_side_payload(
    record: dict[str, Any],
    result: ReduceTapeResult | SwapTapeResult,
    provenance: str,
) -> dict[str, Any]:
    assert result.annual_delta_co2_t is not None
    assert result.cumulative_full_flat_co2_t is not None
    assert result.cumulative_curve_co2_t is not None
    cumulative_curve_t = result.cumulative_curve * KG_TO_TONNES
    return {
        **_common(record, provenance),
        "annual_delta_construction_co2e_t": 0.0,
        "annual_delta_operating_co2e_t": result.annual_delta * KG_TO_TONNES,
        "annual_delta_construction_co2_t": 0.0,
        "annual_delta_operating_co2_t": result.annual_delta_co2_t,
        "gdp_impact_full": result.gdp_impact,
        "cumulative_full_flat_co2e_t": result.cumulative_full_flat * KG_TO_TONNES,
        "cumulative_full_flat_co2_t": result.cumulative_full_flat_co2_t,
        "cumulative_curve_co2e_t": cumulative_curve_t,
        "cumulative_curve_co2_t": result.cumulative_curve_co2_t,
        "copies": _copies(cumulative_curve_t),
        "copies_basis": "floor(abs(cumulative_curve_co2e_t) * intensity_scalar_2050 / 1e9)",
        "jcurve_co2e_t": [
            {"year": int(point["year"]), "value": point["value"] * KG_TO_TONNES} for point in result.jcurve
        ],
    }


def _build_payload(record: dict[str, Any], result: BuildTapeResult, provenance: str) -> dict[str, Any]:
    assert result.annual_delta_construction_co2_t is not None
    assert result.annual_delta_operating_co2_t is not None
    assert result.deltas_by_deployment_co2_t is not None
    assert result.cumulative_full_flat_co2_t is not None
    assert result.cumulative_curve_co2_t is not None
    cumulative_curve_t = result.cumulative_curve * KG_TO_TONNES
    return {
        **_common(record, provenance),
        "annual_delta_construction_co2e_t": result.annual_delta_construction * KG_TO_TONNES,
        "annual_delta_operating_co2e_t": result.annual_delta_operating * KG_TO_TONNES,
        "annual_delta_construction_co2_t": result.annual_delta_construction_co2_t,
        "annual_delta_operating_co2_t": result.annual_delta_operating_co2_t,
        "deltas_by_deployment_co2e_t": {
            fraction: value * KG_TO_TONNES for fraction, value in result.deltas_by_deployment.items()
        },
        "deltas_by_deployment_co2_t": result.deltas_by_deployment_co2_t,
        "gdp_impact_full": result.gdp_impact,
        "cumulative_full_flat_co2e_t": result.cumulative_full_flat * KG_TO_TONNES,
        "cumulative_full_flat_co2_t": result.cumulative_full_flat_co2_t,
        "cumulative_curve_co2e_t": cumulative_curve_t,
        "cumulative_curve_co2_t": result.cumulative_curve_co2_t,
        "copies": _copies(cumulative_curve_t),
        "copies_basis": "floor(abs(cumulative_curve_co2e_t) * intensity_scalar_2050 / 1e9)",
        "jcurve_co2e_t": [
            {"year": int(point["year"]), "value": point["value"] * KG_TO_TONNES} for point in result.jcurve
        ],
    }


def build_tape_table(
    world: pymrio.IOSystem,
    records: dict[str, dict[str, Any]],
    baskets: dict[str, dict[str, float]],
    baseline: str = BASELINE_NAME,
    provenance: str | None = None,
    extension: str = "impacts",
    stressor: str | tuple[str, ...] = GHG_STRESSOR,
    co2_stressor: str | tuple[str, ...] = CO2_STRESSOR,
) -> dict[str, Any]:
    """Solve every ready tape and retain held records without assigning them a score."""
    provenance = provenance or _provenance()
    tapes: dict[str, Any] = {}
    for key, record in records.items():
        if record["status"] != "ready":
            tapes[key] = {**_common(record, provenance), "held_reason": record["beta_day_assumption"].strip()}
        elif record["wing"] == "reduce":
            result = run_reduce_tape(
                world, record, baskets, extension=extension, stressor=stressor, co2_stressor=co2_stressor
            )
            tapes[key] = _y_side_payload(record, result, provenance)
        elif record["wing"] == "swap":
            result = run_swap_tape(
                world, record, baskets, extension=extension, stressor=stressor, co2_stressor=co2_stressor
            )
            tapes[key] = _y_side_payload(record, result, provenance)
        else:
            result = run_build_tape(world, record, extension=extension, stressor=stressor, co2_stressor=co2_stressor)
            tapes[key] = _build_payload(record, result, provenance)

    return {
        "$schema": str(SCHEMA_PATH.relative_to(_REPO_ROOT)),
        "schema_version": 1,
        "baseline": baseline,
        "basis_year": 2011,
        "target_year": TARGET_YEAR,
        "intensity_scalar_2050": intensity_scalar(TARGET_YEAR),
        "units": {
            "co2e": "tonnes CO2-eq",
            "co2": "tonnes CO2",
            "money": "2011 million EUR, basic prices",
        },
        "tapes": tapes,
    }


def write_tape_table(table: dict[str, Any], destination: Path) -> None:
    """Write a table with stable key ordering and formatting."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(table, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    """Load the cached baseline and export ``tape_table_<date>.json``."""
    config = load_config()
    baseline_path = Path(config["data"]["worlds_path"]) / BASELINE_NAME
    world = pymrio.load_all(baseline_path)
    records = load_tape_records()
    baskets = load_scenario_weights()
    validate_baskets(world, {category: list(weights) for category, weights in baskets.items()}, records)
    table = build_tape_table(world, records, baskets)
    destination = DEFAULT_EXPORT_DIR / f"tape_table_{date.today().isoformat()}.json"
    write_tape_table(table, destination)
    print(f"Exported {len(table['tapes'])} tapes to {destination}")


if __name__ == "__main__":
    main()
