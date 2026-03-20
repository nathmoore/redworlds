"""Tests for currency conversion (src/redworlds/engine/currency.py).

All tests use the ``test_mrio`` fixture from conftest.py — no EXIOBASE needed.
"""

import pytest
import pymrio

from redworlds.engine.currency import (
    CONVERSION_FACTOR,
    EUR_USD_2011,
    CPI_2026_OVER_2011,
    meur_2011_to_musd_2026,
    convert_mrio_currency,
)


def test_conversion_factor_matches_constants() -> None:
    """CONVERSION_FACTOR should equal EUR_USD_2011 * CPI_2026_OVER_2011."""
    assert CONVERSION_FACTOR == pytest.approx(EUR_USD_2011 * CPI_2026_OVER_2011)


def test_scalar_conversion_uses_factor() -> None:
    """meur_2011_to_musd_2026(1.0) should equal CONVERSION_FACTOR."""
    assert meur_2011_to_musd_2026(1.0) == pytest.approx(CONVERSION_FACTOR)


def test_scalar_conversion_zero() -> None:
    """Zero in, zero out."""
    assert meur_2011_to_musd_2026(0.0) == pytest.approx(0.0)


def test_mrio_conversion_scales_z(test_mrio: pymrio.IOSystem) -> None:
    """Z matrix should be scaled by CONVERSION_FACTOR after conversion."""
    original_z = test_mrio.Z.copy()
    converted = convert_mrio_currency(test_mrio)
    assert converted.Z.values == pytest.approx(original_z.values * CONVERSION_FACTOR)


def test_mrio_conversion_scales_y(test_mrio: pymrio.IOSystem) -> None:
    """Y matrix should be scaled by CONVERSION_FACTOR after conversion."""
    original_y = test_mrio.Y.copy()
    converted = convert_mrio_currency(test_mrio)
    assert converted.Y.values == pytest.approx(original_y.values * CONVERSION_FACTOR)


def test_mrio_conversion_is_pure(test_mrio: pymrio.IOSystem) -> None:
    """Original mrio should be unchanged after convert_mrio_currency."""
    original_z_values = test_mrio.Z.values.copy()
    convert_mrio_currency(test_mrio)
    assert test_mrio.Z.values == pytest.approx(original_z_values)


def test_mrio_conversion_returns_new_object(test_mrio: pymrio.IOSystem) -> None:
    """convert_mrio_currency should return a different object, not the input."""
    converted = convert_mrio_currency(test_mrio)
    assert converted is not test_mrio
    assert converted.Z is not test_mrio.Z
