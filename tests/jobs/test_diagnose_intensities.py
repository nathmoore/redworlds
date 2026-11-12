"""Tests for the intensity diagnostic (src/redworlds/jobs/diagnose_intensities.py)."""

import pandas as pd
import pytest

from redworlds.jobs.diagnose_intensities import flag_outliers, intensity_table

INDEX = pd.MultiIndex.from_tuples([("North", "steel"), ("South", "steel"), ("Tiny", "steel"), ("North", "wheat")])
OUTPUT = pd.Series([600.0, 399.0, 1.0, 50.0], index=INDEX)
EMISSIONS = pd.Series([600.0, 399.0, 20.0, 5.0], index=INDEX)


def test_world_intensity_is_weighted_by_output() -> None:
    """The world figure is total emissions over total output, not a mean of regional ratios."""
    table = intensity_table(OUTPUT, EMISSIONS).set_index(["region", "product"])

    assert table.loc[("North", "steel"), "world_intensity"] == pytest.approx(1019.0 / 1000.0)
    assert table.loc[("Tiny", "steel"), "intensity"] == pytest.approx(20.0)
    assert table.loc[("Tiny", "steel"), "output_share"] == pytest.approx(0.001)


def test_a_tiny_region_with_an_extreme_intensity_is_flagged_as_a_small_sample() -> None:
    """Twenty times the world intensity on a thousandth of world output is the artefact case."""
    outliers = flag_outliers(intensity_table(OUTPUT, EMISSIONS))

    assert list(outliers["region"]) == ["Tiny"]
    assert bool(outliers.loc[0, "small_sample"])


def test_ordinary_differences_between_regions_are_not_flagged() -> None:
    """Regions close to the world intensity, and single-region products, are left alone."""
    outliers = flag_outliers(intensity_table(OUTPUT, EMISSIONS))

    assert "wheat" not in set(outliers["product"])
    assert "North" not in set(outliers["region"])


def test_cells_with_no_output_are_dropped() -> None:
    """A region that makes none of a product has no intensity to compare."""
    output = pd.Series([10.0, 0.0], index=pd.MultiIndex.from_tuples([("North", "steel"), ("South", "steel")]))
    emissions = pd.Series([10.0, 0.0], index=output.index)

    table = intensity_table(output, emissions)

    assert list(table["region"]) == ["North"]
