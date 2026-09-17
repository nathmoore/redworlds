"""Tests for region aggregation (src/redworlds/engine/regions.py).

Unit tests use the pymrio test world with a test-only concordance in
tests/fixtures/test_world_regions.csv. The integration test uses real EXIOBASE data via the
``exiobase_mrio`` fixture and runs only with ``just test -m integration``.
"""

from pathlib import Path

import pymrio
import pytest

from redworlds.engine.regions import (
    DEFAULT_CONCORDANCE_PATH,
    aggregate_regions,
    load_region_concordance,
)

FIXTURE_PATH = Path(__file__).parents[1] / "fixtures" / "test_world_regions.csv"


@pytest.fixture
def test_concordance() -> dict[str, str]:
    return load_region_concordance(FIXTURE_PATH)


def test_default_concordance_loads_and_names_seven_regions() -> None:
    """The committed EXIOBASE concordance should parse and cover exactly the 7 game regions."""
    concordance = load_region_concordance(DEFAULT_CONCORDANCE_PATH)
    assert len(concordance) == 49
    assert len(set(concordance.values())) == 7


def test_fixture_concordance_loads(test_concordance: dict[str, str]) -> None:
    """The test-world concordance should map all six test regions."""
    assert set(test_concordance) == {"reg1", "reg2", "reg3", "reg4", "reg5", "reg6"}


def test_aggregate_regions_reduces_count(test_mrio: pymrio.IOSystem, test_concordance: dict[str, str]) -> None:
    """Aggregated mrio should have five game regions, down from six test regions."""
    result = aggregate_regions(test_mrio, concordance=test_concordance)
    assert len(list(result.get_regions())) == 5
    assert set(result.get_regions()) == set(test_concordance.values())


def test_aggregate_regions_is_pure(test_mrio: pymrio.IOSystem, test_concordance: dict[str, str]) -> None:
    """aggregate_regions should not mutate the input mrio."""
    original_regions = list(test_mrio.get_regions())
    aggregate_regions(test_mrio, concordance=test_concordance)
    assert list(test_mrio.get_regions()) == original_regions


def test_aggregate_regions_conserves_total_final_demand(
    test_mrio: pymrio.IOSystem, test_concordance: dict[str, str]
) -> None:
    """Summing regions together must not create or destroy final demand."""
    result = aggregate_regions(test_mrio, concordance=test_concordance)
    assert result.Y is not None and test_mrio.Y is not None
    assert result.Y.to_numpy().sum() == pytest.approx(test_mrio.Y.to_numpy().sum())


def test_missing_region_raises(test_mrio: pymrio.IOSystem, test_concordance: dict[str, str]) -> None:
    """A region code absent from the concordance must fail loudly, not silently drop."""
    incomplete = {k: v for k, v in test_concordance.items() if k != "reg6"}
    with pytest.raises(KeyError):
        aggregate_regions(test_mrio, concordance=incomplete)


@pytest.mark.integration
def test_aggregate_regions_integration(exiobase_mrio: pymrio.IOSystem) -> None:
    """Against real EXIOBASE data, the committed concordance should yield exactly 7 regions."""
    result = aggregate_regions(exiobase_mrio)
    assert len(list(result.get_regions())) == 7


@pytest.mark.integration
def test_concordance_covers_exactly_the_exiobase_regions(exiobase_mrio: pymrio.IOSystem) -> None:
    """Every code in the real table is mapped and the CSV carries no code the table lacks."""
    concordance = load_region_concordance(DEFAULT_CONCORDANCE_PATH)
    assert set(concordance) == set(exiobase_mrio.get_regions())


def test_taiwan_sits_in_mainland_east_asia() -> None:
    """Settled 2026-09-17 against the game's regions doc: TW joins CN and KR in region 6."""
    concordance = load_region_concordance(DEFAULT_CONCORDANCE_PATH)
    assert concordance["TW"] == concordance["CN"] == "Mainland East Asia"
