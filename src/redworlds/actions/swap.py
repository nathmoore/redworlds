"""SWAP action: shift a fraction of an IO sector's demand to a cleaner alternative.

The player selects an eco-choice (e.g. heat pumps replacing gas boilers, vegetarian
diet replacing existing diet) and a rollout percentage from the Decarbonator Deck.

Red Worlds then:
1. Reduces the target sector's share of the scenario by ``pct_rollout``.
2. Increases the replacement sector's share by an equivalent amount.
3. Rebalances money flows across the economy to maintain a closed system.

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
