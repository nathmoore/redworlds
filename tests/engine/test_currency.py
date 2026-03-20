"""Tests for currency conversion (src/redworlds/engine/currency.py).

All tests use the ``test_mrio`` fixture from conftest.py — no EXIOBASE needed.
"""

import pymrio
import pytest

from redworlds.engine.currency import (
    CONVERSION_FACTOR,
    CPI_2026_OVER_2011,
    EUR_USD_2011,
    convert_mrio_currency,
    meur_2011_to_musd_2026,
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


def test_mrio_conversion_does_not_touch_extension_F(test_mrio: pymrio.IOSystem) -> None:
    """Raw satellite flows (F) should be unchanged — only monetary matrices are converted."""
    original_F = test_mrio.emissions.F.copy()
    converted = convert_mrio_currency(test_mrio)
    assert converted.emissions.F.values == pytest.approx(original_F.values)


def test_mrio_conversion_preserves_total_emissions(test_mrio: pymrio.IOSystem) -> None:
    """Total emissions D_cba should be scale-invariant under currency conversion.

    Proof: D = S·L·Y. After scaling x and Y by k, S = F·x̂⁻¹ becomes S/k and
    Y becomes Y·k, so D_new = (S/k)·L·(Y·k) = D. Verified here by recalculating
    after conversion.
    """
    original_D = test_mrio.emissions.D_cba.copy()
    converted = convert_mrio_currency(test_mrio)
    converted.calc_all()
    assert converted.emissions.D_cba.values == pytest.approx(original_D.values)
