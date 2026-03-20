"""Tests for region aggregation (src/redworlds/engine/regions.py).

Unit tests require the concordance CSV and an mrio whose region codes are all
present in the mapping. Integration tests require real EXIOBASE data.

These tests are skipped until the concordance is validated against the actual
EXIOBASE pxp data.

TODO: implement — see GitHub issue #N
"""

import pymrio
import pytest

from redworlds.engine.regions import (
    aggregate_regions,
    load_region_concordance,
)


@pytest.mark.skip(reason="concordance not yet validated against real EXIOBASE pxp — see GitHub issue #N")
def test_concordance_loads() -> None:
    """load_region_concordance() should return a non-empty dict."""
    concordance = load_region_concordance()
    assert len(concordance) > 0


@pytest.mark.skip(reason="pymrio test mrio uses different region codes than EXIOBASE — see GitHub issue #N")
def test_aggregate_regions_reduces_count(test_mrio: pymrio.IOSystem) -> None:
    """Aggregated mrio should have fewer regions than the input."""
    result = aggregate_regions(test_mrio)
    assert len(list(result.get_regions())) < len(list(test_mrio.get_regions()))


@pytest.mark.skip(reason="concordance not yet validated against real EXIOBASE pxp — see GitHub issue #N")
def test_aggregate_regions_is_pure(test_mrio: pymrio.IOSystem) -> None:
    """aggregate_regions should not mutate the input mrio."""
    original_regions = list(test_mrio.get_regions())
    aggregate_regions(test_mrio)
    assert list(test_mrio.get_regions()) == original_regions


@pytest.mark.integration
@pytest.mark.skip(reason="concordance not yet validated against real EXIOBASE pxp — see GitHub issue #N")
def test_aggregate_regions_integration(exiobase_mrio: pymrio.IOSystem) -> None:
    """Against real EXIOBASE data, aggregated mrio should have exactly 7 regions."""
    result = aggregate_regions(exiobase_mrio)
    assert len(list(result.get_regions())) == 7
