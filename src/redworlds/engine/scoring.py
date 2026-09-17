"""Scoring: turn a shocked world into the numbers the game shows.

The game scores one tape as cumulative CO2 abated over 2050–2100 against a do-nothing
baseline. For the MVP this is a static comparative in the sense of Wiebe et al. (2018):
one Leontief solve for the shocked world, the annual emissions difference against the
baseline, and that difference spread across the window through a deployment curve.

For BUILD tapes the curve has two parts: construction years, where the injected capex
emits (positive delta, the rising side of the J-curve), and operating years, where the
new technology mix displaces emissions (negative delta). SWAP and REDUCE ramp along their
deployment curve from year one.

Results are meaningful relative to the baseline, never as absolute levels.

References:
  - docs/design/red_carbon_contract.md §1 and §4.3 — the score and the result shape
  - docs/design/game_mechanics.md — result_json
  - docs/design/assumptions.md — "MVP scoring is a static comparative"
"""

from collections.abc import Sequence

import pymrio

from redworlds.engine.io_tables import GHG_EXTENSION, GHG_STRESSOR

WINDOW_START: int = 2050
WINDOW_END: int = 2100

# The game charts the J-curve in five-year blocks, not year by year
# (docs/design/red_carbon_contract.md §4.3).
JCURVE_STEP_YEARS: int = 5


def total_emissions(
    mrio: pymrio.IOSystem,
    extension: str = GHG_EXTENSION,
    stressor: str | tuple[str, ...] = GHG_STRESSOR,
) -> float:
    """World total consumption-based emissions, in the extension's units.

    Sums one stressor row of pymrio's ``D_cba_reg`` across every region. Because the
    accounting is consumption-based, the regional footprints partition world emissions:
    adding them up double-counts nothing. Requires a calculated system.

    Args:
        mrio: A calculated IO system with the named extension.
        extension: Name of the satellite account. EXIOBASE: ``"impacts"``.
        stressor: Row label within the account. A tuple for multi-level indices, as in
            pymrio's test world.

    Returns:
        Annual world total as a float (kg CO2-eq for EXIOBASE).
    """
    account = getattr(mrio, extension)
    return float(account.D_cba_reg.loc[stressor].sum())


def annual_delta(
    baseline: pymrio.IOSystem,
    shocked: pymrio.IOSystem,
    extension: str = GHG_EXTENSION,
    stressor: str | tuple[str, ...] = GHG_STRESSOR,
) -> float:
    """Total annual GHG difference between a shocked world and the baseline, at full deployment.

    Both systems must be calculated. The comparison is a world total: a tape played in one
    region is credited with the emissions it moves anywhere, including the leakage of
    production shifting abroad.

    Args:
        baseline: The calculated do-nothing world.
        shocked: The calculated world after a tape's shock.
        extension: Name of the satellite account. EXIOBASE: ``"impacts"``.
        stressor: Row label within the account.

    Returns:
        ``shocked − baseline`` in the extension's units (kg CO2-eq for EXIOBASE).
        Negative means the shock abates.
    """
    return total_emissions(shocked, extension, stressor) - total_emissions(baseline, extension, stressor)


def cumulative_delta(
    delta_at_full_deployment: float,
    deployment_curve: Sequence[float],
    start_year: int = WINDOW_START,
    end_year: int = WINDOW_END,
) -> dict:
    """Spread an annual delta across the window and sum it.

    Each year's value is ``delta_at_full_deployment × deployment_curve[year]``. The delta
    keeps the sign ``annual_delta`` gave it (negative = abatement) and the curve is the
    deployed fraction, 0 → 1, so SWAP and REDUCE are one call each.

    BUILD is two calls added together: the construction-phase delta (positive: the capex
    emits) through a curve that is 1 during the build years and 0 after, plus the
    operating-phase delta (negative: the new plant displaces) through a curve that is 0
    during the build years and ramps up afterwards. Summing the two jcurves gives the
    J shape. Keeping the phases separate is deliberate: they are different shocks with
    different annual deltas, and one curve with a sign flip would hide that.

    Args:
        delta_at_full_deployment: Annual emissions difference once the intervention is fully
            deployed (from ``annual_delta``), signed.
        deployment_curve: One multiplier per year from ``start_year`` to ``end_year``
            inclusive, in [0, 1]. 0 = not yet deployed, 1 = fully deployed.
        start_year: First year of the window.
        end_year: Last year of the window.

    Returns:
        ``{"co2_delta_cumulative": float, "jcurve": [{"year": int, "value": float}, ...]}``
        with the curve in five-year blocks, matching docs/design/game_mechanics.md.

    Raises:
        ValueError: If the curve does not have exactly one multiplier per year in the window.
    """
    years = list(range(start_year, end_year + 1))
    if len(deployment_curve) != len(years):
        raise ValueError(
            f"deployment_curve must have one multiplier per year from {start_year} to {end_year} "
            f"inclusive ({len(years)} values); got {len(deployment_curve)}"
        )

    annual_values = [delta_at_full_deployment * multiplier for multiplier in deployment_curve]
    jcurve = [
        {"year": year, "value": value}
        for year, value in zip(years, annual_values, strict=True)
        if (year - start_year) % JCURVE_STEP_YEARS == 0
    ]
    return {"co2_delta_cumulative": sum(annual_values), "jcurve": jcurve}


def gdp_impact(baseline: pymrio.IOSystem, shocked: pymrio.IOSystem) -> float:
    """Change in world final demand between a shocked world and the baseline.

    This is the "booked GDP reduction" of a REDUCE tape under rule RE2: the spend that
    simply leaves the model instead of being re-spent elsewhere
    (docs/design/red_carbon_contract.md §3). SWAP preserves the total and BUILD injects,
    so for those wings this number is near zero or positive.

    The figure is a world total in the table's monetary unit (M.EUR for EXIOBASE).
    Attributing the contraction to individual regions via value added is a later
    refinement — see docs/backlog.md.

    Args:
        baseline: The do-nothing world.
        shocked: The world after a tape's shock.

    Returns:
        ``shocked − baseline`` summed over the whole ``Y`` matrix. Negative means the
        economy contracted.
    """
    assert baseline.Y is not None and shocked.Y is not None
    shocked_total = float(shocked.Y.to_numpy().sum())
    baseline_total = float(baseline.Y.to_numpy().sum())
    return shocked_total - baseline_total
