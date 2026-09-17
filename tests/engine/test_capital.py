"""Tests for capital endogenisation (src/redworlds/engine/capital.py).

Unit tests run on the pymrio test world with a synthetic capital use matrix: a small,
plausible slice of each region's gross investment spread across its using sectors. What
they check is the accounting, not the numbers — the same identities must hold whatever
the classification.

Integration tests (``-m integration``) load the real 9800 x 9800 Kbar for EXIOBASE 3.8.2
pxp 2011 and put it through the full system. They are slow: the recalculation inverts a
9800 x 9800 matrix.
"""

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pymrio
import pytest

from redworlds.config import load_config
from redworlds.engine.capital import GFCF_COLUMN, endogenise_capital, load_capital_use

# Share of a region's gross investment that the synthetic Kbar treats as depreciation.
SYNTHETIC_DEPRECIATION_SHARE = 0.4


def _table(mrio: pymrio.IOSystem, name: str) -> Any:
    """Fetch a pymrio table or extension; they are Optional / dynamic, which upsets the type checker."""
    table = getattr(mrio, name)
    assert table is not None, f"{name} is not set — has the system been calculated?"
    return table


@pytest.fixture
def synthetic_capital_use(test_mrio: pymrio.IOSystem) -> pd.DataFrame:
    """A plausible capital use matrix for the test world, indexed exactly like ``Z``.

    Each region depreciates ``SYNTHETIC_DEPRECIATION_SHARE`` of its GFCF column, split
    across that region's using sectors in proportion to their output. Rows therefore keep
    the real mix of capital goods and columns stay smaller than the industries using them.
    """
    gfcf = _table(test_mrio, "Y").loc[:, (slice(None), GFCF_COLUMN)] * SYNTHETIC_DEPRECIATION_SHARE
    output = _table(test_mrio, "x")["indout"]

    capital_use = pd.DataFrame(0.0, index=_table(test_mrio, "Z").index, columns=_table(test_mrio, "Z").columns)
    for region in test_mrio.get_regions():
        users = output[region]
        weights = users / users.sum()
        capital_good = gfcf[(region, GFCF_COLUMN)]
        capital_use.loc[:, region] = np.outer(capital_good.to_numpy(), weights.to_numpy())
    return capital_use


def test_capital_coefficients_are_added_to_a(test_mrio, synthetic_capital_use) -> None:
    """A_new must equal A + Kbar · x̂⁻¹."""
    result = endogenise_capital(test_mrio, synthetic_capital_use)

    expected_k = synthetic_capital_use.div(_table(test_mrio, "x")["indout"], axis="columns")
    expected_a = _table(test_mrio, "A") + expected_k

    assert np.allclose(_table(result, "A").to_numpy(), expected_a.to_numpy())


def test_gfcf_falls_by_the_capital_used_in_that_region(test_mrio, synthetic_capital_use) -> None:
    """Each region's GFCF column loses exactly what that region's industries consumed."""
    result = endogenise_capital(test_mrio, synthetic_capital_use)

    for region in test_mrio.get_regions():
        removed = _table(test_mrio, "Y")[(region, GFCF_COLUMN)] - _table(result, "Y")[(region, GFCF_COLUMN)]
        used_here = synthetic_capital_use.loc[:, region].sum(axis="columns")
        assert np.allclose(removed.to_numpy(), used_here.to_numpy())


def test_other_final_demand_columns_are_untouched(test_mrio, synthetic_capital_use) -> None:
    """Households, government, exports and the rest keep their original values."""
    result = endogenise_capital(test_mrio, synthetic_capital_use)

    other = [column for column in _table(test_mrio, "Y").columns if column[1] != GFCF_COLUMN]
    pd.testing.assert_frame_equal(_table(result, "Y")[other], _table(test_mrio, "Y")[other])


def test_flow_removed_from_gfcf_equals_flow_endogenised(test_mrio, synthetic_capital_use) -> None:
    """Before any re-solve, every euro taken out of GFCF is a euro of capital use.

    This is the conservation statement that actually holds. Once ``calc_all()`` re-solves
    the system, A and Y have both changed, so x changes too and Z_new is not Z_old + Kbar.
    """
    result = endogenise_capital(test_mrio, synthetic_capital_use)

    removed_from_y = (_table(test_mrio, "Y") - _table(result, "Y")).sum(axis="columns")
    endogenised = synthetic_capital_use.sum(axis="columns")

    assert np.allclose(removed_from_y.to_numpy(), endogenised.to_numpy())
    assert removed_from_y.sum() == pytest.approx(synthetic_capital_use.to_numpy().sum())


def test_recalculated_system_is_consistent(test_mrio, synthetic_capital_use) -> None:
    """After calc_all() the endogenised system satisfies x = L·y with the new A."""
    result = endogenise_capital(test_mrio, synthetic_capital_use)
    result.calc_all()

    y = _table(result, "Y").sum(axis="columns")
    assert np.allclose(_table(result, "x")["indout"].to_numpy(), _table(result, "L").to_numpy() @ y.to_numpy())
    # Z must be the new A scaled by the new output, not the old flows carried over.
    assert np.allclose(
        _table(result, "Z").to_numpy(), _table(result, "A").to_numpy() * _table(result, "x")["indout"].to_numpy()
    )
    # Endogenising capital adds to A, so every industry needs at least as much output.
    assert (_table(result, "x")["indout"] >= _table(test_mrio, "x")["indout"] - 1e-6).all()


def test_endogenise_capital_is_pure(test_mrio, synthetic_capital_use) -> None:
    """The input mrio must not be mutated."""
    original_a = _table(test_mrio, "A").copy()
    original_y = _table(test_mrio, "Y").copy()
    original_z = _table(test_mrio, "Z").copy()

    result = endogenise_capital(test_mrio, synthetic_capital_use)
    result.calc_all()

    assert result is not test_mrio
    pd.testing.assert_frame_equal(_table(test_mrio, "A"), original_a)
    pd.testing.assert_frame_equal(_table(test_mrio, "Y"), original_y)
    pd.testing.assert_frame_equal(_table(test_mrio, "Z"), original_z)


def test_satellite_flows_are_untouched(test_mrio, synthetic_capital_use) -> None:
    """F and F_Y carry over unchanged; only the derived coefficients are recalculated."""
    result = endogenise_capital(test_mrio, synthetic_capital_use)
    result.calc_all()

    pd.testing.assert_frame_equal(_table(result, "emissions").F, _table(test_mrio, "emissions").F)
    pd.testing.assert_frame_equal(_table(result, "emissions").F_Y, _table(test_mrio, "emissions").F_Y)


def test_zero_output_sector_gets_zero_coefficient(test_mrio, synthetic_capital_use) -> None:
    """A sector with no output must get a zero capital coefficient, not an infinity."""
    idle = _table(test_mrio, "x").index[0]
    _table(test_mrio, "x").loc[idle, "indout"] = 0.0

    result = endogenise_capital(test_mrio, synthetic_capital_use)

    assert np.isfinite(_table(result, "A").to_numpy()).all()
    assert np.allclose(_table(result, "A")[idle].to_numpy(), _table(test_mrio, "A")[idle].to_numpy())


@pytest.mark.integration
def test_real_capital_use_matches_exiobase_labels(exiobase_mrio) -> None:
    """The Zenodo Kbar must line up cell-for-cell with the EXIOBASE Z it will be added to."""
    capital_use = load_capital_use(Path(load_config()["data"]["capital_use_path"]))

    assert capital_use.shape == _table(exiobase_mrio, "Z").shape
    pd.testing.assert_index_equal(capital_use.index, _table(exiobase_mrio, "Z").index)
    pd.testing.assert_index_equal(capital_use.columns, _table(exiobase_mrio, "Z").columns)


@pytest.mark.integration
def test_real_capital_use_is_a_plausible_share_of_investment(exiobase_mrio) -> None:
    """Consumption of fixed capital is positive and smaller than gross investment."""
    capital_use = load_capital_use(Path(load_config()["data"]["capital_use_path"]))

    kbar_total = capital_use.to_numpy().sum()
    gfcf_total = _table(exiobase_mrio, "Y").loc[:, (slice(None), GFCF_COLUMN)].to_numpy().sum()

    assert kbar_total > 0, f"Kbar total {kbar_total:,.0f} M EUR"
    assert kbar_total < gfcf_total, (
        f"Kbar total {kbar_total:,.0f} M EUR should be below GFCF total {gfcf_total:,.0f} M EUR "
        f"(ratio {kbar_total / gfcf_total:.3f})"
    )


@pytest.mark.integration
def test_real_system_recalculates_after_endogenisation(exiobase_mrio) -> None:
    """The full 9800 x 9800 system still solves once capital is in A. Slow: minutes."""
    capital_use = load_capital_use(Path(load_config()["data"]["capital_use_path"]))

    result = endogenise_capital(exiobase_mrio, capital_use)
    result.calc_all()

    y = _table(result, "Y").sum(axis="columns")
    assert np.allclose(_table(result, "x")["indout"].to_numpy(), _table(result, "L").to_numpy() @ y.to_numpy())
    assert np.isfinite(_table(result, "A").to_numpy()).all()
