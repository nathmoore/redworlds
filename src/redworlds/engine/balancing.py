"""Economic rebalancing to maintain a closed IO economy after a player action.

After BUILD and SWAP actions, money flows must be rebalanced so that total
output equals total input across all sectors. REDUCE actions deliberately do
NOT call these functions — see docs/design/assumptions.md.

All functions are pure: they receive an IOSystem and return an updated one
without mutating the original.

References:
  - docs/design/assumptions.md — rebalancing approach and post-growth rationale
  - docs/design/game_mechanics.md — which actions trigger rebalancing
"""

import pymrio


def rebalance_economy(
    mrio: pymrio.IOSystem,
    changed_region: str,
    changed_sector: str,
) -> pymrio.IOSystem:
    """Rebalance money flows across all sectors after a change to one sector.

    Redistributes the change in spending to maintain a closed economy. The specific
    rebalancing method is documented in docs/design/assumptions.md.

    Called automatically by apply_build() and apply_swap(); never by apply_reduce().

    Args:
        mrio: The IO system after a sector change (a copy is returned).
        changed_region: The region where the change was applied.
        changed_sector: The sector that was directly modified.

    Returns:
        IO system with money flows rebalanced across the economy.

    TODO: implement — see GitHub issue #14
    """
    raise NotImplementedError
