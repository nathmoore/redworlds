"""Run a tape record against the cached baseline and return its numbers.

This is the layer between a tape record and the engine. `apply_reduce` takes a region
label, a list of product labels and a fraction; a record carries a region *id*, a scenario
category and a ceiling. Translating one into the other is deliberately not the engine's
job — engine functions stay pure and know nothing about the game's tape ids.

Y-side REDUCE and SWAP shocks are solved once at full deployment. BUILD operation changes
``A`` and is not linear after the Leontief inverse is rebuilt, so it is solved at 0.25,
0.5, 0.75 and 1.0. The export gives the game those four points for interpolation.

References:
  - docs/design/red_carbon_contract.md §4.4 — the precomputed table and why one solve is enough
  - docs/backlog.md — T3
"""

from dataclasses import dataclass
from typing import Any

import pymrio

from redworlds.actions.build import apply_build_construction, apply_build_operation
from redworlds.actions.reduce import apply_reduce
from redworlds.actions.swap import apply_swap
from redworlds.engine.io_tables import (
    CONSUMPTION_CATEGORIES,
    GHG_EXTENSION,
    GHG_STRESSOR,
    HOUSEHOLDS,
)
from redworlds.engine.regions import load_region_names
from redworlds.engine.scoring import (
    WINDOW_END,
    WINDOW_START,
    annual_delta,
    build_deployment_curves,
    combine_jcurves,
    cumulative_delta,
    deployment_curve,
    gdp_impact,
)
from redworlds.jobs.tape_records import weights_for

# Fully deployed from the first year of the window. The game applies a tape's real ramp
# itself, so what the table ships is the flat figure and the shape is the game's business.
FLAT_CURVE: tuple[float, ...] = tuple(1.0 for _ in range(WINDOW_START, WINDOW_END + 1))
BUILD_DEPLOYMENT_SAMPLES: tuple[float, ...] = (0.25, 0.5, 0.75, 1.0)
GG_TO_TONNES: float = 1e3


@dataclass(frozen=True)
class ReduceTapeResult:
    """One REDUCE tape solved at full deployment, in the table's own units.

    Attributes:
        key: The tape id the game sends.
        region: The region label the shock was applied to.
        pct_reduction: The record's headline fraction. A product's realised cut is this
            times its weight, so for a weighted basket it is not the cut of anything.
        products: How many products the basket held, for a sanity check at export.
        annual_delta: kg CO2-eq per year, signed. Negative means the tape abates.
        gdp_impact: Change in world final demand, in the table's monetary unit. Negative
            means the economy contracted, which under rule RE2 is what REDUCE does.
        cumulative_full_flat: kg CO2-eq over 2050–2100 at flat deployment.
        jcurve: Five-yearly points across the window, as the game charts them.
    """

    key: str
    region: str
    pct_reduction: float
    products: int
    annual_delta: float
    gdp_impact: float
    cumulative_full_flat: float
    jcurve: list[dict[str, float]]
    cumulative_curve: float
    annual_delta_co2_t: float | None = None
    cumulative_full_flat_co2_t: float | None = None
    cumulative_curve_co2_t: float | None = None


@dataclass(frozen=True)
class SwapTapeResult:
    """One closed-budget SWAP tape solved at full deployment."""

    key: str
    region: str
    pct_rollout: float
    products: int
    annual_delta: float
    gdp_impact: float
    cumulative_full_flat: float
    cumulative_curve: float
    jcurve: list[dict[str, float]]
    annual_delta_co2_t: float | None = None
    cumulative_full_flat_co2_t: float | None = None
    cumulative_curve_co2_t: float | None = None


@dataclass(frozen=True)
class BuildTapeResult:
    """Construction and sampled operation results for one BUILD tape."""

    key: str
    region: str
    build_years: int
    annual_delta_construction: float
    annual_delta_operating: float
    deltas_by_deployment: dict[str, float]
    gdp_impact: float
    cumulative_full_flat: float
    cumulative_curve: float
    jcurve: list[dict[str, float]]
    annual_delta_construction_co2_t: float | None = None
    annual_delta_operating_co2_t: float | None = None
    deltas_by_deployment_co2_t: dict[str, float] | None = None
    cumulative_full_flat_co2_t: float | None = None
    cumulative_curve_co2_t: float | None = None


def run_reduce_tape(
    world: pymrio.IOSystem,
    record: dict[str, Any],
    baskets: dict[str, dict[str, float]],
    region_names: dict[int, str] | None = None,
    extension: str = GHG_EXTENSION,
    stressor: str | tuple[str, ...] = GHG_STRESSOR,
    co2_stressor: str | tuple[str, ...] | None = None,
) -> ReduceTapeResult:
    """Solve one REDUCE tape against the baseline at its full ceiling.

    Args:
        world: The calculated baseline — the cached aggregated world in practice.
        record: One record from ``tape_records.load_tape_records``, wing ``reduce``.
        baskets: As ``tape_records.load_scenario_weights`` returns.
        region_names: {game_region_id: label}. Loaded from the concordance if omitted.
        extension: Name of the satellite account to score on. EXIOBASE: ``"impacts"``.
        stressor: Row label within the account. A tuple for multi-level indices, as in
            pymrio's test world.

    Returns:
        The tape's numbers at full deployment.

    Raises:
        ValueError: If the record is not a REDUCE record.
    """
    if record["wing"] != "reduce":
        raise ValueError(f"{record['key']!r} is a {record['wing']} tape; run_reduce_tape takes reduce tapes")

    region_names = load_region_names() if region_names is None else region_names
    region = region_names[record["region_id"]]
    weights = weights_for(record, baskets)
    pct_reduction = record["max_reducible_fraction"]

    shocked = apply_reduce(
        world,
        region,
        list(weights),
        pct_reduction,
        categories=record.get("final_demand_categories", CONSUMPTION_CATEGORIES),
        direct_emissions_extension=record.get("direct_emissions_extension"),
        weights=weights,
        direct_emissions_driver=record.get("direct_emissions_driver"),
    )

    delta = annual_delta(world, shocked, extension, stressor)
    spread = cumulative_delta(delta, FLAT_CURVE)
    curved = cumulative_delta(delta, deployment_curve())
    co2_delta_t = None
    co2_flat_t = None
    co2_curve_t = None
    if co2_stressor is not None:
        co2_delta_t = annual_delta(world, shocked, extension, co2_stressor) * GG_TO_TONNES
        co2_flat_t = cumulative_delta(co2_delta_t, FLAT_CURVE)["co2_delta_cumulative"]
        co2_curve_t = cumulative_delta(co2_delta_t, deployment_curve())["co2_delta_cumulative"]
    return ReduceTapeResult(
        key=record["key"],
        region=region,
        pct_reduction=pct_reduction,
        products=len(weights),
        annual_delta=delta,
        gdp_impact=gdp_impact(world, shocked),
        cumulative_full_flat=spread["co2_delta_cumulative"],
        jcurve=curved["jcurve"],
        cumulative_curve=curved["co2_delta_cumulative"],
        annual_delta_co2_t=co2_delta_t,
        cumulative_full_flat_co2_t=co2_flat_t,
        cumulative_curve_co2_t=co2_curve_t,
    )


def run_swap_tape(
    world: pymrio.IOSystem,
    record: dict[str, Any],
    baskets: dict[str, dict[str, float]],
    region_names: dict[int, str] | None = None,
    extension: str = GHG_EXTENSION,
    stressor: str | tuple[str, ...] = GHG_STRESSOR,
    co2_stressor: str | tuple[str, ...] | None = None,
) -> SwapTapeResult:
    """Solve one consumer-side SWAP tape at its full ceiling."""
    if record["wing"] != "swap":
        raise ValueError(f"{record['key']!r} is a {record['wing']} tape; run_swap_tape takes swap tapes")
    region_names = load_region_names() if region_names is None else region_names
    region = region_names[record["region_id"]]
    weights = weights_for(record, baskets)
    rollout = record["max_replaceable_fraction"]
    shocked = apply_swap(
        world,
        region,
        list(weights),
        record["replacement_sector"],
        rollout,
        replacement_ratio=record["replacement_ratio"],
        categories=record.get("final_demand_categories", (HOUSEHOLDS,)),
        direct_emissions_extension=record.get("direct_emissions_extension"),
        weights=weights,
        direct_emissions_driver=record.get("direct_emissions_driver"),
    )
    delta = annual_delta(world, shocked, extension, stressor)
    flat = cumulative_delta(delta, FLAT_CURVE)
    curved = cumulative_delta(delta, deployment_curve())
    co2_delta_t = None
    co2_flat_t = None
    co2_curve_t = None
    if co2_stressor is not None:
        co2_delta_t = annual_delta(world, shocked, extension, co2_stressor) * GG_TO_TONNES
        co2_flat_t = cumulative_delta(co2_delta_t, FLAT_CURVE)["co2_delta_cumulative"]
        co2_curve_t = cumulative_delta(co2_delta_t, deployment_curve())["co2_delta_cumulative"]
    return SwapTapeResult(
        key=record["key"],
        region=region,
        pct_rollout=rollout,
        products=len(weights),
        annual_delta=delta,
        gdp_impact=gdp_impact(world, shocked),
        cumulative_full_flat=flat["co2_delta_cumulative"],
        cumulative_curve=curved["co2_delta_cumulative"],
        jcurve=curved["jcurve"],
        annual_delta_co2_t=co2_delta_t,
        cumulative_full_flat_co2_t=co2_flat_t,
        cumulative_curve_co2_t=co2_curve_t,
    )


def run_build_tape(
    world: pymrio.IOSystem,
    record: dict[str, Any],
    region_names: dict[int, str] | None = None,
    extension: str = GHG_EXTENSION,
    stressor: str | tuple[str, ...] = GHG_STRESSOR,
    co2_stressor: str | tuple[str, ...] | None = None,
) -> BuildTapeResult:
    """Solve one BUILD tape's construction phase and four operating deployment points."""
    if record["wing"] != "build":
        raise ValueError(f"{record['key']!r} is a {record['wing']} tape; run_build_tape takes build tapes")
    region_names = load_region_names() if region_names is None else region_names
    region = region_names[record["region_id"]]
    build_years = record["build_years_reference"]
    construction = apply_build_construction(
        world,
        region,
        record["budget_musd_2026_purchaser"] / build_years,
        capex_split=record.get("capex_split", None)
        or {
            "Construction work (45)": 0.40,
            "Machinery and equipment n.e.c. (29)": 0.42,
            "Electrical machinery and apparatus n.e.c. (31)": 0.09,
            "Other business services (74)": 0.09,
        },
        reallocate=record.get("reallocate", False),
    )
    construction_delta = annual_delta(world, construction, extension, stressor)

    operating_worlds = {
        fraction: apply_build_operation(
            world,
            region,
            record["technology_sector"],
            record["cover_magnitude"]["twh_per_year"],
            fraction,
            fossil_sectors=record.get("fossil_sectors", None)
            or (
                "Electricity by coal",
                "Electricity by gas",
                "Electricity by petroleum and other oil derivatives",
            ),
            energy_extension=record.get("energy_extension", "satellite"),
            energy_stressor=record.get("energy_stressor", "Energy Carrier Supply: Total"),
        )
        for fraction in BUILD_DEPLOYMENT_SAMPLES
    }
    samples = {
        str(fraction): annual_delta(world, shocked, extension, stressor)
        for fraction, shocked in operating_worlds.items()
    }
    operating_delta = samples["1.0"]
    construction_curve, operating_curve = build_deployment_curves(build_years)
    construction_spread = cumulative_delta(construction_delta, construction_curve)
    operating_spread = cumulative_delta(operating_delta, operating_curve)
    jcurve = combine_jcurves(construction_spread["jcurve"], operating_spread["jcurve"])

    construction_co2_t = None
    operating_co2_t = None
    sample_co2_t = None
    flat_co2_t = None
    curve_co2_t = None
    if co2_stressor is not None:
        construction_co2_t = annual_delta(world, construction, extension, co2_stressor) * GG_TO_TONNES
        sample_co2_t = {
            str(fraction): annual_delta(world, shocked, extension, co2_stressor) * GG_TO_TONNES
            for fraction, shocked in operating_worlds.items()
        }
        operating_co2_t = sample_co2_t["1.0"]
        flat_co2_t = cumulative_delta(operating_co2_t, FLAT_CURVE)["co2_delta_cumulative"]
        curve_co2_t = (
            cumulative_delta(construction_co2_t, construction_curve)["co2_delta_cumulative"]
            + cumulative_delta(operating_co2_t, operating_curve)["co2_delta_cumulative"]
        )

    return BuildTapeResult(
        key=record["key"],
        region=region,
        build_years=build_years,
        annual_delta_construction=construction_delta,
        annual_delta_operating=operating_delta,
        deltas_by_deployment=samples,
        gdp_impact=gdp_impact(world, construction),
        cumulative_full_flat=cumulative_delta(operating_delta, FLAT_CURVE)["co2_delta_cumulative"],
        cumulative_curve=(construction_spread["co2_delta_cumulative"] + operating_spread["co2_delta_cumulative"]),
        jcurve=jcurve,
        annual_delta_construction_co2_t=construction_co2_t,
        annual_delta_operating_co2_t=operating_co2_t,
        deltas_by_deployment_co2_t=sample_co2_t,
        cumulative_full_flat_co2_t=flat_co2_t,
        cumulative_curve_co2_t=curve_co2_t,
    )


def run_ready_reduce_tapes(
    world: pymrio.IOSystem,
    records: dict[str, dict[str, Any]],
    baskets: dict[str, dict[str, float]],
    extension: str = GHG_EXTENSION,
    stressor: str | tuple[str, ...] = GHG_STRESSOR,
) -> dict[str, ReduceTapeResult]:
    """Solve every REDUCE tape marked ready, keyed by tape id.

    Records marked ``pending`` are skipped rather than failed: the BUILD and SWAP records
    carry their fields so the export schema is right first time, but nothing can solve them
    until sprint 3.

    Args:
        world: The calculated baseline.
        records: As ``tape_records.load_tape_records`` returns.
        baskets: As ``tape_records.load_scenario_weights`` returns.
        extension: Name of the satellite account to score on. EXIOBASE: ``"impacts"``.
        stressor: Row label within the account.

    Returns:
        One result per ready REDUCE tape.
    """
    region_names = load_region_names()
    return {
        key: run_reduce_tape(world, record, baskets, region_names, extension, stressor)
        for key, record in records.items()
        if record["wing"] == "reduce" and record["status"] == "ready"
    }
