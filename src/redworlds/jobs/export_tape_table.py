"""Solve the committed tapes and write the deterministic table consumed by Red Carbon.

All nine records are executable. A provisional result is usable for the MVP but carries a
named material limitation. BUILD and grid operating shocks are sampled at four deployment
fractions because changing ``A`` and re-inverting the Leontief matrix is non-linear.
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
from redworlds.engine.io_tables import CO2_STRESSOR, GHG_STRESSOR, emissions_to_tonnes
from redworlds.jobs.build_baseline import BASELINE_NAME
from redworlds.jobs.run_tapes import (
    BuildTapeResult,
    ReduceTapeResult,
    SwapTapeResult,
    run_build_tape,
    run_grid_tape,
    run_lifetime_tape,
    run_reduce_tape,
    run_swap_tape,
)
from redworlds.jobs.tape_records import (
    load_scenario_lifetimes,
    load_scenario_weights,
    load_tape_records,
    validate_baskets,
)

_REPO_ROOT = Path(__file__).parents[3]
DEFAULT_EXPORT_DIR = _REPO_ROOT / "data" / "exports"
SCHEMA_PATH = _REPO_ROOT / "data" / "tech_choices" / "tape_table.schema.json"
# A brick is what the peg delivers, not a round billion.
#
# eca_nuclear's ten-reactor cover is the peg (red_carbon_contract.md §2): brick-calibrated
# covers are sized to match it, so the unit has to *be* it. Ten reactors measure 1.267 Gt
# CO2e on the 2011 table, which the 2050 intensity correction takes to 0.555 Gt — and that
# is the brick. A record may instead name a physical-ceiling cover when one brick is not
# physically available; Smart Grid is the first such case.
#
# Declared rather than derived from nuclear's solve, to keep the unit from moving underfoot
# whenever the table is rebuilt: a brick that silently re-based itself would re-scale every
# other tape's copies with nothing failing. `test_the_brick_is_the_peg` asserts the two agree,
# so a genuine change to nuclear breaks the build and the constant is updated deliberately.
BRICK_TONNES: float = 5.55e8
SOLVABLE_STATUSES: tuple[str, ...] = ("ready", "provisional")


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
        dirty = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no"],
            cwd=_REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        if dirty:
            commit += "+dirty"
    except (FileNotFoundError, subprocess.CalledProcessError):
        commit = "unknown"
    return f"jobs/export_tape_table.py @ {commit}"


# Which fields carry which year, because one table holds both.
#
# The contract has the game apply intensity_scalar_2050 (red_carbon_contract.md 4), so every
# tonne field here is on the 2011 basis. But a brick *is* the 2050 peg, so bricks_at_cover and
# copies must already carry the scalar or they could not be compared with it — and that leaves
# two bases in one object with nothing on the fields to say so. A reader comparing a 2011 tonne
# against a 2050 brick is out by the scalar and nothing fails.
#
# Naming them is the cheap half of the fix. The field names stay as they are because the game's
# PHP reads them (class-redcarbon-game-engine-table.php), so a rename is a cross-repo change for
# a labelling problem. The whole distinction disappears when the SSP2 walk replaces the scalar
# with a real 2050 world — see docs/backlog.md and issue #17.
TONNE_FIELD_BASIS_YEAR: int = 2011
PRESCALED_FIELDS: tuple[str, ...] = ("bricks_at_cover", "copies")


def _basis_note() -> dict[str, Any]:
    """State which fields are on the 2011 basis and which already carry the 2050 scalar."""
    return {
        "tonne_fields_year": TONNE_FIELD_BASIS_YEAR,
        "prescaled_fields": list(PRESCALED_FIELDS),
        "note": (
            "Every *_co2e_t and *_co2_t field, including jcurve_co2e_t values, is on the "
            f"{TONNE_FIELD_BASIS_YEAR} basis: multiply by intensity_scalar_2050 to state it in "
            f"{TARGET_YEAR} intensities. The fields in prescaled_fields already have that "
            "scalar applied, because a brick is the peg measured in "
            f"{TARGET_YEAR} intensities. Do not apply it twice."
        ),
    }


def _common(record: dict[str, Any], provenance: str) -> dict[str, Any]:
    common = {
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
    if record["status"] == "provisional":
        common["limitation"] = record["beta_day_assumption"].strip()
    return common


def _copies(cumulative_curve_t: float) -> int:
    """Whole abatement bricks delivered; a backfire cannot become positive via ``abs``."""
    return max(0, math.floor(-cumulative_curve_t * intensity_scalar(TARGET_YEAR) / BRICK_TONNES))


def _cover_reading(record: dict[str, Any], cumulative_curve_t: float, solved_at: str) -> dict[str, Any]:
    """State a tape's value at its *cover* magnitude, which is what covers are calibrated on.

    Two different quantities have been called "the brick reading". ``cumulative_curve_co2e_t``
    is whatever deployment the tape was solved at, and that differs by wing: a BUILD tape is
    solved at its cover, a Y-side tape at its ceiling. Reporting both under one name is how a
    calibration pass ends up comparing a cover against a ceiling without noticing.

    So this emits the cover figure explicitly, plus the scale between cover and ceiling, plus
    a sentence naming which is which. Where the two are not linearly related the fields are
    ``None`` rather than a plausible wrong number — see ``cover_basis``.
    """
    cover_key = record.get("ceiling_cover_key")
    if cover_key is None:
        reason = (
            "cover and ceiling are not linearly related, so the cover figure needs its own solve"
            if record.get("cover_scaling") == "non-linear"
            else "no ceiling_cover_key: this tape's cover has no single magnitude to scale by"
        )
        return {
            "cumulative_at_cover_co2e_t": None,
            "bricks_at_cover": None,
            "regional_ceiling_scale": None,
            "cover_basis": f"solved at {solved_at}; {reason}",
        }

    scale = record["regional_ceiling"] / record["cover_magnitude"][cover_key]
    at_cover = cumulative_curve_t if solved_at == "cover" else cumulative_curve_t / scale
    calibration = record.get("cover_calibration", "brick")
    basis = (
        f"solved at {solved_at}; ceiling is {scale:g}x the cover of "
        f"{record['cover_magnitude'][cover_key]:g} {cover_key}"
    )
    if calibration == "physical_ceiling":
        basis += "; cover is the full physical programme, not calibrated to one brick"
    return {
        "cumulative_at_cover_co2e_t": at_cover,
        "bricks_at_cover": -at_cover * intensity_scalar(TARGET_YEAR) / BRICK_TONNES,
        "regional_ceiling_scale": scale,
        "cover_basis": basis,
    }


def _y_side_payload(
    record: dict[str, Any],
    result: ReduceTapeResult | SwapTapeResult,
    provenance: str,
    co2e_to_tonnes: float,
    cover_result: ReduceTapeResult | None = None,
) -> dict[str, Any]:
    assert result.annual_delta_co2_t is not None
    assert result.cumulative_full_flat_co2_t is not None
    assert result.cumulative_curve_co2_t is not None
    cumulative_curve_t = result.cumulative_curve * co2e_to_tonnes
    payload = {
        **_common(record, provenance),
        "annual_delta_construction_co2e_t": 0.0,
        "annual_delta_operating_co2e_t": result.annual_delta * co2e_to_tonnes,
        "annual_delta_construction_co2_t": 0.0,
        "annual_delta_operating_co2_t": result.annual_delta_co2_t,
        "gdp_impact_full": result.gdp_impact,
        "cumulative_full_flat_co2e_t": result.cumulative_full_flat * co2e_to_tonnes,
        "cumulative_full_flat_co2_t": result.cumulative_full_flat_co2_t,
        "cumulative_curve_co2e_t": cumulative_curve_t,
        "cumulative_curve_co2_t": result.cumulative_curve_co2_t,
        **_cover_reading(record, cumulative_curve_t, "ceiling"),
        "copies": _copies(cumulative_curve_t),
        "copies_basis": "max(0, floor(-cumulative_curve_co2e_t * intensity_scalar_2050 / brick_co2e_t))",
        "jcurve_co2e_t": [
            {"year": int(point["year"]), "value": point["value"] * co2e_to_tonnes} for point in result.jcurve
        ],
    }
    if cover_result is not None:
        cover_curve_t = cover_result.cumulative_curve * co2e_to_tonnes
        payload.update(
            {
                "cumulative_at_cover_co2e_t": cover_curve_t,
                "bricks_at_cover": -cover_curve_t * intensity_scalar(TARGET_YEAR) / BRICK_TONNES,
                "regional_ceiling_scale": None,
                "cover_basis": "cover and ceiling solved separately from N / (mean life + N); not linearly scaled",
            }
        )
    return payload


def _build_payload(
    record: dict[str, Any], result: BuildTapeResult, provenance: str, co2e_to_tonnes: float
) -> dict[str, Any]:
    assert result.annual_delta_construction_co2_t is not None
    assert result.annual_delta_operating_co2_t is not None
    assert result.deltas_by_deployment_co2_t is not None
    assert result.cumulative_full_flat_co2_t is not None
    assert result.cumulative_curve_co2_t is not None
    cumulative_curve_t = result.cumulative_curve * co2e_to_tonnes
    ceiling_scale = None
    copies = None
    if record["regional_ceiling"] > 0.0:
        cover_key = record["ceiling_cover_key"]
        ceiling_scale = record["regional_ceiling"] / record["cover_magnitude"][cover_key]
        copies = _copies(cumulative_curve_t * ceiling_scale)
    return {
        **_common(record, provenance),
        "annual_delta_construction_co2e_t": result.annual_delta_construction * co2e_to_tonnes,
        "annual_delta_operating_co2e_t": result.annual_delta_operating * co2e_to_tonnes,
        "annual_delta_construction_co2_t": result.annual_delta_construction_co2_t,
        "annual_delta_operating_co2_t": result.annual_delta_operating_co2_t,
        "deltas_by_deployment_co2e_t": {
            fraction: value * co2e_to_tonnes for fraction, value in result.deltas_by_deployment.items()
        },
        "deltas_by_deployment_co2_t": result.deltas_by_deployment_co2_t,
        "gdp_impact_full": result.gdp_impact,
        "cumulative_full_flat_co2e_t": result.cumulative_full_flat * co2e_to_tonnes,
        "cumulative_full_flat_co2_t": result.cumulative_full_flat_co2_t,
        "cumulative_curve_co2e_t": cumulative_curve_t,
        "cumulative_curve_co2_t": result.cumulative_curve_co2_t,
        **_cover_reading(record, cumulative_curve_t, "cover"),
        "copies": copies,
        "copies_basis": (
            "max(0, floor(-cumulative_curve_co2e_t * intensity_scalar_2050 * regional_ceiling_scale / brick_co2e_t))"
        ),
        "jcurve_co2e_t": [
            {"year": int(point["year"]), "value": point["value"] * co2e_to_tonnes} for point in result.jcurve
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
    region_names: dict[int, str] | None = None,
    mean_lives: dict[str, dict[str, float]] | None = None,
) -> dict[str, Any]:
    """Solve ready and provisional tapes; retain held records without assigning a score."""
    provenance = provenance or _provenance()
    co2e_to_tonnes = emissions_to_tonnes(world, 1.0, extension, stressor)
    tapes: dict[str, Any] = {}
    for key, record in records.items():
        if record["status"] not in SOLVABLE_STATUSES:
            tapes[key] = {**_common(record, provenance), "held_reason": record["beta_day_assumption"].strip()}
        elif record.get("mechanism") == "grid_efficiency":
            result = run_grid_tape(
                world,
                record,
                region_names=region_names,
                extension=extension,
                stressor=stressor,
                co2_stressor=co2_stressor,
            )
            tapes[key] = _build_payload(record, result, provenance, co2e_to_tonnes)
        elif record.get("mechanism") == "product_lifetime_extension":
            if mean_lives is None:
                mean_lives = load_scenario_lifetimes()
            result, cover_result = run_lifetime_tape(
                world,
                record,
                baskets,
                mean_lives,
                region_names=region_names,
                extension=extension,
                stressor=stressor,
                co2_stressor=co2_stressor,
            )
            tapes[key] = _y_side_payload(record, result, provenance, co2e_to_tonnes, cover_result=cover_result)
        elif record["wing"] == "reduce":
            result = run_reduce_tape(
                world,
                record,
                baskets,
                region_names=region_names,
                extension=extension,
                stressor=stressor,
                co2_stressor=co2_stressor,
            )
            tapes[key] = _y_side_payload(record, result, provenance, co2e_to_tonnes)
        elif record["wing"] == "swap":
            result = run_swap_tape(
                world,
                record,
                baskets,
                region_names=region_names,
                extension=extension,
                stressor=stressor,
                co2_stressor=co2_stressor,
            )
            tapes[key] = _y_side_payload(record, result, provenance, co2e_to_tonnes)
        else:
            result = run_build_tape(
                world,
                record,
                region_names=region_names,
                extension=extension,
                stressor=stressor,
                co2_stressor=co2_stressor,
            )
            tapes[key] = _build_payload(record, result, provenance, co2e_to_tonnes)

    return {
        "$schema": str(SCHEMA_PATH.relative_to(_REPO_ROOT)),
        "schema_version": 1,
        "baseline": baseline,
        "basis_year": 2011,
        "target_year": TARGET_YEAR,
        "intensity_scalar_2050": intensity_scalar(TARGET_YEAR),
        "brick_co2e_t": BRICK_TONNES,
        "units": {
            "co2e": "tonnes CO2-eq",
            "co2": "tonnes CO2",
            "money": "2011 million EUR, basic prices",
        },
        "basis": _basis_note(),
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
    mean_lives = load_scenario_lifetimes()
    validate_baskets(world, {category: list(weights) for category, weights in baskets.items()}, records)
    table = build_tape_table(world, records, baskets, mean_lives=mean_lives)
    destination = DEFAULT_EXPORT_DIR / f"tape_table_{date.today().isoformat()}.json"
    write_tape_table(table, destination)
    print(f"Exported {len(table['tapes'])} tapes to {destination}")


if __name__ == "__main__":
    main()
