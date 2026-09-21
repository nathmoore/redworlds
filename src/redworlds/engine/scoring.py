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
DEFAULT_RAMP_YEARS: int = 10
BUILD_OPERATION_RAMP_YEARS: int = 5


def deployment_curve(ramp_years: int = DEFAULT_RAMP_YEARS) -> tuple[float, ...]:
    """Return the default SWAP/REDUCE ramp across the scoring window.

    Deployment reaches 10%, 20%, ... 100% in the first ten years and stays there. Its
    multipliers sum to 46.5 over the 51-year inclusive window, or 0.912 of a flat curve.
    """
    if ramp_years <= 0:
        raise ValueError(f"ramp_years must be positive; got {ramp_years}")
    years = range(WINDOW_START, WINDOW_END + 1)
    return tuple(min((year - WINDOW_START + 1) / ramp_years, 1.0) for year in years)


def build_deployment_curves(
    build_years: int,
    operating_ramp_years: int = BUILD_OPERATION_RAMP_YEARS,
) -> tuple[tuple[float, ...], tuple[float, ...]]:
    """Return separate construction and operating curves for a BUILD tape.

    Construction is flat for ``build_years``. Operation is zero until completion, then
    reaches 20%, 40%, ... 100% over five years. For a ten-year build the operating curve
    sums to 39, or 0.765 of a 51-year flat solve; for fusion's twenty years it sums to 29,
    or 0.569. These are the sizing corrections documented in tape_records.md §9.2.
    """
    if build_years <= 0:
        raise ValueError(f"build_years must be positive; got {build_years}")
    if operating_ramp_years <= 0:
        raise ValueError(f"operating_ramp_years must be positive; got {operating_ramp_years}")
    window_length = WINDOW_END - WINDOW_START + 1
    if build_years >= window_length:
        raise ValueError(f"build_years must be shorter than the {window_length}-year scoring window")

    construction = tuple(1.0 if offset < build_years else 0.0 for offset in range(window_length))
    operating = tuple(
        0.0 if offset < build_years else min((offset - build_years + 1) / operating_ramp_years, 1.0)
        for offset in range(window_length)
    )
    return construction, operating


def combine_jcurves(*curves: Sequence[dict[str, float]]) -> list[dict[str, float]]:
    """Add aligned five-yearly J-curves, preserving their shared years."""
    if not curves:
        return []
    years = [point["year"] for point in curves[0]]
    if any([point["year"] for point in curve] != years for curve in curves[1:]):
        raise ValueError("jcurves must contain the same years in the same order")
    return [{"year": year, "value": sum(curve[index]["value"] for curve in curves)} for index, year in enumerate(years)]


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
