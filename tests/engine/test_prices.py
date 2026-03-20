"""Tests for price type conversion (src/redworlds/engine/prices.py)."""

import pytest

from redworlds.engine.prices import (
    BASIC_TO_PURCHASER_MARKUP,
    basic_to_purchaser,
    purchaser_to_basic,
)


def test_markup_constant_is_above_one() -> None:
    """Purchaser prices must be higher than basic prices."""
    assert BASIC_TO_PURCHASER_MARKUP > 1.0


def test_basic_to_purchaser_applies_markup() -> None:
    """basic_to_purchaser(100) should equal 100 * BASIC_TO_PURCHASER_MARKUP."""
    assert basic_to_purchaser(100.0) == pytest.approx(100.0 * BASIC_TO_PURCHASER_MARKUP)


def test_purchaser_to_basic_reverses_markup() -> None:
    """purchaser_to_basic(120) should equal 120 / BASIC_TO_PURCHASER_MARKUP."""
    assert purchaser_to_basic(120.0) == pytest.approx(120.0 / BASIC_TO_PURCHASER_MARKUP)


def test_round_trip() -> None:
    """Converting basic → purchaser → basic should return the original value."""
    value = 543.21
    assert purchaser_to_basic(basic_to_purchaser(value)) == pytest.approx(value)


def test_zero_input() -> None:
    """Zero in, zero out for both directions."""
    assert basic_to_purchaser(0.0) == pytest.approx(0.0)
    assert purchaser_to_basic(0.0) == pytest.approx(0.0)
