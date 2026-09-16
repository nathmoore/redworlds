"""Tests for capital endogenisation (src/redworlds/engine/capital.py).

When implemented, these tests should verify, on the pymrio test world with a synthetic
capital use matrix:
- A gains the coefficient-form K (A_new == A + Kbar · x̂⁻¹)
- The GFCF column(s) of Y fall by the endogenised flows; other Y columns are unchanged
- Total final demand plus intermediate demand is conserved (the flow moved, not vanished)
- The returned IO system is a new object (original not mutated)
- Satellite accounts (F) are untouched

TODO: implement — see docs/backlog.md §Sequencing (GitHub issue pending)
"""

import pytest

from redworlds.engine.capital import endogenise_capital, load_capital_use  # noqa: F401


@pytest.mark.skip(reason="endogenise_capital not yet implemented — see docs/backlog.md")
def test_endogenise_capital_moves_flow_from_y_to_a(test_mrio):
    """Endogenised capital should leave Y + Z totals unchanged while shifting flow into A."""
    pass


@pytest.mark.skip(reason="endogenise_capital not yet implemented — see docs/backlog.md")
def test_endogenise_capital_is_pure(test_mrio):
    """The input mrio must not be mutated."""
    pass
