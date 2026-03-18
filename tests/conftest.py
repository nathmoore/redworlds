"""Shared pytest fixtures for Red Worlds tests.

The primary fixture is ``test_mrio`` — a small, fast pymrio.IOSystem built from
pymrio's built-in test data. This is the default IO system used in unit tests.
No EXIOBASE files are required.

For integration tests that run against real EXIOBASE data, use the
``@pytest.mark.integration`` marker and access the ``exiobase_mrio`` fixture.
Integration tests are skipped by default; run them with:

    just test -m integration

(Requires config/config.toml pointing at a local EXIOBASE download.)
"""

import pymrio
import pytest


@pytest.fixture
def test_mrio() -> pymrio.IOSystem:
    """Return a small pymrio IO system for fast unit testing.

    Uses pymrio's built-in test IO world — no external data files required.
    The system is fully calculated (calc_all() has been called).
    """
    mrio = pymrio.load_test()
    mrio.calc_all()
    return mrio


def pytest_configure(config: pytest.Config) -> None:
    """Register custom pytest markers."""
    config.addinivalue_line(
        "markers",
        "integration: mark test as requiring real EXIOBASE data (skipped by default)",
    )
