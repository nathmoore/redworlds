"""Tests for the intensity correction seam (src/redworlds/engine/intensity.py).

There is not much behaviour here, which is the point: the module exists so the 2011 → 2050
simplification has one name and one home, and so replacing either stage with real data is one
edit rather than a search. What these tests pin is the contract that replacement must keep —
above all that the two stages stay separable, because one is observation and one is scenario.
"""

import pytest

from redworlds.engine.intensity import (
    BASE_YEAR,
    OBSERVED_2011_TO_2027,
    PIVOT_YEAR,
    SCENARIO_2027_TO_2050,
    TARGET_YEAR,
    intensity_scalar,
)


def test_defaults_to_the_target_year() -> None:
    """Callers that do not care which year should get the game's own."""
    assert intensity_scalar() == intensity_scalar(TARGET_YEAR)


def test_the_base_year_needs_no_correction() -> None:
    """The table is already 2011, so correcting it to 2011 must be the identity."""
    assert intensity_scalar(BASE_YEAR) == 1.0


def test_the_stages_compose_by_multiplication() -> None:
    """2050 is the observed half times the scenario half, and nothing else.

    If this ever stops holding, the two stages have been entangled and replacing one without
    the other has become impossible — which is the whole thing the split exists to prevent.
    """
    assert intensity_scalar(TARGET_YEAR) == pytest.approx(intensity_scalar(PIVOT_YEAR) * SCENARIO_2027_TO_2050)
    assert intensity_scalar(PIVOT_YEAR) == OBSERVED_2011_TO_2027


def test_each_stage_makes_the_world_cleaner_per_euro() -> None:
    """Both stages must sit in (0, 1).

    Above 1.0 claims the world gets dirtier per unit of demand; at or below 0 flips the sign
    of every abatement in the export.
    """
    assert 0.0 < OBSERVED_2011_TO_2027 < 1.0
    assert 0.0 < SCENARIO_2027_TO_2050 < 1.0
    assert 0.0 < intensity_scalar(TARGET_YEAR) < intensity_scalar(PIVOT_YEAR) < 1.0


def test_an_unsupported_year_raises_rather_than_interpolating() -> None:
    """Silently returning the 2050 factor for 2035 would be wrong by a decade, with no sign."""
    with pytest.raises(ValueError, match="answers for"):
        intensity_scalar(2035)


def test_the_correction_preserves_sign_and_shrinks_the_number() -> None:
    """Abatement stays negative, and 2050 abates less per euro than 2011 would."""
    abatement = -389e9  # kg CO2e/yr, roughly the buy-less tape on the 2011 table
    corrected = intensity_scalar() * abatement

    assert corrected < 0
    assert abs(corrected) < abs(abatement)
