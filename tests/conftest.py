"""Shared pytest fixtures for Red Worlds tests.

The primary fixture is ``test_mrio`` — a small, fast pymrio.IOSystem built from
pymrio's built-in test data. This is the default IO system used in unit tests.
No EXIOBASE files are required.

Integration tests against real EXIOBASE data are marked ``@pytest.mark.integration``
and use the ``exiobase_mrio`` fixture. They are deselected unless you run:

    just test -m integration

and skipped if config/config.toml or the EXIOBASE download is missing.
"""

from pathlib import Path

import pymrio
import pytest

from redworlds.config import load_config


@pytest.fixture
def test_mrio() -> pymrio.IOSystem:
    """Return a small pymrio IO system for fast unit testing.

    Uses pymrio's built-in test IO world — no external data files required.
    The system is fully calculated (calc_all() has been called).
    """
    mrio = pymrio.load_test()
    mrio.calc_all()
    return mrio


@pytest.fixture(scope="session")
def exiobase_mrio() -> pymrio.IOSystem:
    """Return the real EXIOBASE 3.8.2 pxp 2011 system, calculated. Slow; session-scoped.

    Skips (rather than fails) when the personal config or the download is absent, so the
    integration suite is safe to run on any machine.
    """
    try:
        cfg = load_config()
    except FileNotFoundError as exc:
        pytest.skip(f"integration tests need config/config.toml: {exc}")
    path = Path(cfg["data"]["exiobase_path"]) / "IOT_2011_pxp"
    if not path.exists():
        pytest.skip(f"EXIOBASE not found at {path} — see data/README.md")
    mrio = pymrio.parse_exiobase3(path)
    mrio.calc_all()
    return mrio


def pytest_configure(config: pytest.Config) -> None:
    """Register custom pytest markers."""
    config.addinivalue_line(
        "markers",
        "integration: mark test as requiring real EXIOBASE data (deselected unless -m integration)",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Skip integration tests unless the user explicitly asked for them with -m."""
    if "integration" in (config.getoption("-m") or ""):
        return
    skip = pytest.mark.skip(reason="integration test — run with `just test -m integration`")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip)
