"""Tests for the BUILD action (src/redworlds/actions/build.py).

All tests use the ``test_mrio`` fixture from conftest.py — no EXIOBASE needed.

When implemented, these tests should verify:
- CapEx is correctly spread over the build period (budget / build_years per year)
- The energy mix is only updated after the build period completes
- The returned IO system is a new object (original not mutated)
- Economy is rebalanced after the build (total output conserved)
- Invalid region or technology raises a clear error

TODO: implement — see GitHub issue #6
"""

import numpy as np
import pymrio
import pytest

from redworlds.actions.build import apply_build, apply_build_construction, apply_build_operation
from redworlds.engine.currency import CONVERSION_FACTOR
from redworlds.engine.io_tables import GFCF, HOUSEHOLDS
from redworlds.engine.prices import purchaser_to_basic


def test_build_spreads_capex_linearly(test_mrio: pymrio.IOSystem) -> None:
    """CapEx should be evenly distributed across the build period."""
    split = {"food": 0.4, "mining": 0.6}
    result = apply_build(
        mrio=test_mrio,
        region="reg1",
        technology="offshore_wind",
        budget=1_000_000,
        build_years=5,
        current_year=1,
        capex_split=split,
    )
    assert result is not test_mrio, "apply_build should return a new IO system"
    assert result.Y is not None and test_mrio.Y is not None
    added = float((result.Y - test_mrio.Y).to_numpy().sum())
    assert added == pytest.approx(purchaser_to_basic(1_000_000) / CONVERSION_FACTOR / 5)
    assert result.Y.loc[("reg1", "food"), ("reg1", GFCF)] - test_mrio.Y.loc[
        ("reg1", "food"), ("reg1", GFCF)
    ] == pytest.approx(added * 0.4)


def test_build_after_construction_is_identity(test_mrio: pymrio.IOSystem) -> None:
    result = apply_build(test_mrio, "reg1", "nuclear", 100.0, 5, 6, {"food": 1.0})
    assert result.Y is not None and test_mrio.Y is not None
    assert result.Y.equals(test_mrio.Y)


def test_build_reallocation_is_budget_neutral(test_mrio: pymrio.IOSystem) -> None:
    result = apply_build_construction(test_mrio, "reg1", 1.0, {"food": 1.0}, reallocate=True)
    assert result.Y is not None and test_mrio.Y is not None
    assert float(result.Y.to_numpy().sum()) == pytest.approx(float(test_mrio.Y.to_numpy().sum()))


def test_build_can_be_paid_for_by_households_weighted_by_elasticity(test_mrio: pymrio.IOSystem) -> None:
    """Household-funded reallocation leaves investment alone and takes most from the high-weight product."""
    assert test_mrio.Y is not None

    def build(weights: dict[str, float] | None) -> pymrio.IOSystem:
        return apply_build_construction(
            test_mrio,
            "reg1",
            1_000.0,
            {"food": 1.0},
            reallocate=True,
            reallocate_from=(HOUSEHOLDS,),
            reallocation_weights=weights,
        )

    flat = build(None)
    weighted = build({"transport": 3.0})
    assert flat.Y is not None and weighted.Y is not None

    injected = purchaser_to_basic(1_000.0) / CONVERSION_FACTOR
    gfcf_change = float((weighted.Y[("reg1", GFCF)] - test_mrio.Y[("reg1", GFCF)]).sum())
    assert gfcf_change == pytest.approx(injected)
    assert float(weighted.Y.to_numpy().sum()) == pytest.approx(float(test_mrio.Y.to_numpy().sum()))
    transport = (slice(None), "transport")
    households = ("reg1", HOUSEHOLDS)
    assert weighted.Y.loc[transport, households].sum() < flat.Y.loc[transport, households].sum()


def test_build_operation_preserves_a_and_y_column_totals(test_mrio: pymrio.IOSystem) -> None:
    """The operating shock changes the electricity recipe, not the size of demand."""
    assert test_mrio.A is not None and test_mrio.Y is not None
    result = apply_build_operation(
        test_mrio,
        "reg1",
        "mining",
        generation_twh=0.001,
        fossil_sectors=("food",),
        energy_extension="emissions",
        energy_stressor=("emission_type1", "air"),
    )
    assert result.A is not None and result.Y is not None
    assert result.L is not None and test_mrio.L is not None
    assert np.allclose(result.A.loc[:, ("reg1", slice(None))].sum(), test_mrio.A.loc[:, ("reg1", slice(None))].sum())
    assert np.allclose(result.Y.loc[:, ("reg1", slice(None))].sum(), test_mrio.Y.loc[:, ("reg1", slice(None))].sum())
    assert not np.allclose(result.L.to_numpy(), test_mrio.L.to_numpy())


def test_build_operation_rejects_more_than_the_fossil_pool(test_mrio: pymrio.IOSystem) -> None:
    with pytest.raises(ValueError, match="exceeds"):
        apply_build_operation(
            test_mrio,
            "reg1",
            "mining",
            generation_twh=1e12,
            fossil_sectors=("food",),
            energy_extension="emissions",
            energy_stressor=("emission_type1", "air"),
        )
