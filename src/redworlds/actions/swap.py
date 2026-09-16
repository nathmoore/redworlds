"""SWAP action: shift a fraction of an IO sector's demand to a cleaner alternative.

The tape names a from-product and a to-product; the game's outcome fraction times the
tape's max_replaceable_fraction gives the rollout percentage.

Red Worlds then:
1. Reduces the target sector's share of the scenario by ``pct_rollout``.
2. Increases the replacement sector's share by an equivalent amount.
3. Rebalances money flows across the economy to maintain a closed system — the
   re-spend is the rebound, by design (docs/design/assumptions.md).

References:
  - docs/design/game_mechanics.md — SWAP input/output contract
  - data/tech_choices/options.toml — compatible eco-choices and scenario tags
"""

import pymrio


def apply_swap(
    mrio: pymrio.IOSystem,
    region: str,
    from_technology: str,
    to_technology: str,
    pct_rollout: float,
) -> pymrio.IOSystem:
    """Apply a SWAP action to a player's IO system.

    Shifts ``pct_rollout`` percent of ``from_technology`` demand in ``region``
    to ``to_technology``, then rebalances the economy.

    Args:
        mrio: The player's current IO system (will not be mutated; a copy is returned).
        region: Amalgamated game region (e.g. "Europe and Central Asia").
        from_technology: Sector key being replaced (e.g. "gas_heating").
        to_technology: Replacement sector key (e.g. "heat_pumps").
        pct_rollout: Fraction of ``from_technology`` demand to shift, in [0.0, 1.0].

    Returns:
        Updated IO system with the sector swap applied.

    TODO: implement — see GitHub issue #7
    """
    raise NotImplementedError
