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

WINDOW_START: int = 2050
WINDOW_END: int = 2100


def annual_delta(baseline: pymrio.IOSystem, shocked: pymrio.IOSystem, extension: str = "impacts") -> float:
    """Total annual GHG difference between a shocked world and the baseline, at full deployment.

    Both systems must be calculated. The returned value is in the extension's units
    (kg CO2-eq for EXIOBASE); negative means the shock abates.

    TODO: implement — see docs/backlog.md §Sequencing (GitHub issue pending)
    """
    raise NotImplementedError


def cumulative_delta(
    delta_at_full_deployment: float,
    deployment_curve: Sequence[float],
    start_year: int = WINDOW_START,
    end_year: int = WINDOW_END,
) -> dict:
    """Spread an annual delta across the window and sum it.

    Args:
        delta_at_full_deployment: Annual emissions difference once the intervention is fully
            deployed (from ``annual_delta``). For BUILD, pass the operating-phase delta and
            supply the construction hump through the curve's positive early values.
        deployment_curve: One multiplier per year from ``start_year`` to ``end_year``
            inclusive, in [−1, 1]. 0 = not yet deployed, 1 = fully deployed; positive values
            in early years model construction emissions.
        start_year: First year of the window.
        end_year: Last year of the window.

    Returns:
        ``{"co2_delta_cumulative": float, "jcurve": [{"year": int, "value": float}, ...]}``
        with the curve in five-year blocks, matching docs/design/game_mechanics.md.

    TODO: implement — see docs/backlog.md §Sequencing (GitHub issue pending)
    """
    raise NotImplementedError
