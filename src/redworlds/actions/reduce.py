"""REDUCE action: decrease consumption of a sector — with no economic rebalancing.

The tape names a basket of products; the game's outcome fraction times the tape's
max_reducible_fraction gives the reduction percentage.

Red Worlds then:
1. Reduces the target sector's final demand by ``pct_reduction``.
2. Does NOT rebalance the rest of the economy. The spend leaves the model and the
   caller reports the GDP impact.

This is a deliberate post-growth design choice (confirmed 2026-09-16): reduced
consumption is not redirected elsewhere and takes no rebound haircut.
See docs/design/assumptions.md for the rationale.

References:
  - docs/design/game_mechanics.md — REDUCE input/output contract
  - docs/design/assumptions.md — post-growth rebalancing assumption
  - data/tech_choices/options.toml — compatible eco-sufficiency choices and scenario tags
"""

import pymrio


def apply_reduce(
    mrio: pymrio.IOSystem,
    region: str,
    sector: str,
    pct_reduction: float,
) -> pymrio.IOSystem:
    """Apply a REDUCE action to a player's IO system.

    Reduces final demand for ``sector`` in ``region`` by ``pct_reduction``.
    Unlike BUILD and SWAP, no rebalancing is performed — this is post-growth behaviour.

    Args:
        mrio: The player's current IO system (will not be mutated; a copy is returned).
        region: Amalgamated game region (e.g. "Europe and Central Asia").
        sector: Sector key being reduced (e.g. "residential_heating").
        pct_reduction: Fraction of demand to remove, in [0.0, 1.0].

    Returns:
        Updated IO system with demand reduced and no rebalancing applied.

    TODO: implement — see GitHub issue #8
    """
    raise NotImplementedError
