"""Run a tape record against the cached baseline and return its numbers.

This is the layer between a tape record and the engine. `apply_reduce` takes a region
label, a list of product labels and a fraction; a record carries a region *id*, a scenario
category and a ceiling. Translating one into the other is deliberately not the engine's
job — engine functions stay pure and know nothing about the game's tape ids.

**Every tape is solved once, at full deployment**, and the game scales the result by the
realised outcome fraction. That works because a Y-side shock is exactly linear in the
fraction: scaling final demand by ``1 − f·m`` scales the change in ``Y`` linearly in ``f``,
``x = L·y`` is linear, and the consumption-based accounts are linear in ``x``. The F_Y
correction is a scale factor on a column and is linear too. ``test_run_tapes`` asserts this
rather than trusting it, because the whole precomputed-table design rests on it
(docs/design/red_carbon_contract.md §4.4).

BUILD and SWAP tapes are not run here. They need the A-matrix and re-spend machinery that
sprint 3 builds (T4–T6), and their records are marked ``status = "pending"`` until then.

References:
  - docs/design/red_carbon_contract.md §4.4 — the precomputed table and why one solve is enough
  - docs/backlog.md — T3
"""

from dataclasses import dataclass
from typing import Any

import pymrio

from redworlds.actions.reduce import apply_reduce
from redworlds.engine.io_tables import CONSUMPTION_CATEGORIES, GHG_EXTENSION, GHG_STRESSOR
from redworlds.engine.regions import load_region_names
from redworlds.engine.scoring import WINDOW_END, WINDOW_START, annual_delta, cumulative_delta, gdp_impact
from redworlds.jobs.tape_records import weights_for

# Fully deployed from the first year of the window. The game applies a tape's real ramp
# itself, so what the table ships is the flat figure and the shape is the game's business.
FLAT_CURVE: tuple[float, ...] = tuple(1.0 for _ in range(WINDOW_START, WINDOW_END + 1))


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


def run_reduce_tape(
    world: pymrio.IOSystem,
    record: dict[str, Any],
    baskets: dict[str, dict[str, float]],
    region_names: dict[int, str] | None = None,
    extension: str = GHG_EXTENSION,
    stressor: str | tuple[str, ...] = GHG_STRESSOR,
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
    return ReduceTapeResult(
        key=record["key"],
        region=region,
        pct_reduction=pct_reduction,
        products=len(weights),
        annual_delta=delta,
        gdp_impact=gdp_impact(world, shocked),
        cumulative_full_flat=spread["co2_delta_cumulative"],
        jcurve=spread["jcurve"],
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
