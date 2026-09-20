"""Tests for the intensity correction seam (src/redworlds/engine/intensity.py).

There is not much behaviour here yet, which is the point: the module exists so that the
2011 → 2050 simplification has one name and one home, and so that replacing it with the real
walk is one edit rather than a search. What these tests pin is the contract that replacement
has to keep.
"""

import pytest

from redworlds.engine.intensity import BASE_YEAR, INTENSITY_SCALAR_2050, TARGET_YEAR, intensity_scalar


def test_defaults_to_the_target_year() -> None:
    """Callers that do not care which year should get the game's own."""
    assert intensity_scalar() == intensity_scalar(TARGET_YEAR)


def test_the_scalar_makes_2050_cleaner_than_2011() -> None:
    """A euro removed in 2050 must carry less carbon than the same euro in 2011.

    Below 1.0 or the correction is claiming the world gets dirtier per unit of demand, and
    above 0 or it flips the sign of every abatement in the export.
    """
    assert 0.0 < INTENSITY_SCALAR_2050 < 1.0


def test_an_unsupported_year_raises_rather_than_guessing() -> None:
    """Silently returning the 2050 factor for 2035 would be wrong by a decade, with no sign."""
    with pytest.raises(ValueError, match="only answers for"):
        intensity_scalar(2035)

    with pytest.raises(ValueError, match="only answers for"):
        intensity_scalar(BASE_YEAR)


def test_the_correction_preserves_sign() -> None:
    """Abatement is negative and must stay negative once corrected."""
    abatement = -389e9  # kg CO2e/yr, roughly the buy-less tape
    assert intensity_scalar() * abatement < 0
    assert abs(intensity_scalar() * abatement) < abs(abatement)
