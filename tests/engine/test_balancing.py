"""Tests for economic balancing (src/redworlds/engine/balancing.py).

All tests use the ``test_mrio`` fixture from conftest.py — no EXIOBASE needed.

When implemented, these tests should verify:
- rebalance_economy returns a new IO system (original not mutated)
- Total output is conserved across the economy after rebalancing
- Rebalancing a system with no changes returns an effectively identical system
- The changed sector's new value is preserved after rebalancing

TODO: implement — see docs/backlog.md §Sequencing (GitHub issue pending)
"""

import numpy as np
import pymrio
import pytest

from redworlds.engine.balancing import rebalance_economy
from redworlds.engine.io_tables import GFCF, HOUSEHOLDS


def test_rebalance_adds_exact_amount_without_mutating_input(test_mrio: pymrio.IOSystem) -> None:
    """Re-spend changes Y by exactly the requested amount on a copy."""
    assert test_mrio.Y is not None
    before = test_mrio.Y.copy()
    result = rebalance_economy(test_mrio, "reg1", 123.0)
    assert result is not test_mrio, "should return a new object"
    assert result.Y is not None
    assert float(result.Y.to_numpy().sum() - before.to_numpy().sum()) == pytest.approx(123.0)
    assert test_mrio.Y.equals(before)


def test_rebalance_keeps_the_flat_proportional_basket(test_mrio: pymrio.IOSystem) -> None:
    """Every positive cell gets the same percentage change under flat proportional weighting."""
    assert test_mrio.Y is not None
    result = rebalance_economy(test_mrio, "reg1", 100.0)
    assert result.Y is not None
    before = test_mrio.Y.loc[:, ("reg1", HOUSEHOLDS)]
    after = result.Y.loc[:, ("reg1", HOUSEHOLDS)]
    positive = before > 0.0
    ratios = (after[positive] / before[positive]).to_numpy()
    assert np.allclose(ratios, ratios[0])


def test_rebalance_can_withdraw_from_gfcf_and_exclude_a_sector(test_mrio: pymrio.IOSystem) -> None:
    assert test_mrio.Y is not None
    protected = test_mrio.Y.loc[(slice(None), "food"), ("reg1", GFCF)].copy()
    result = rebalance_economy(test_mrio, "reg1", -1.0, categories=(GFCF,), excluded_sectors=("food",))
    assert result.Y is not None
    assert result.Y.loc[(slice(None), "food"), ("reg1", GFCF)].equals(protected)


def test_rebalance_rejects_an_empty_selection(test_mrio: pymrio.IOSystem) -> None:
    with pytest.raises(ValueError, match="basket is empty"):
        rebalance_economy(test_mrio, "reg1", 1.0, excluded_sectors=list(test_mrio.get_sectors()))
