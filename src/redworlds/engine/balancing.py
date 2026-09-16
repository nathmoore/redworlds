"""Economic rebalancing to maintain a closed IO economy after a player action.

After a SWAP (and a BUILD under the reallocation flag), money not spent on the
displaced product is re-spent elsewhere so total final demand is preserved. REDUCE
actions deliberately do NOT call these functions: the spend leaves the model
(docs/design/assumptions.md, confirmed 2026-09-16).

The weighting that decides where re-spent money goes is one argument: flat proportional
(placeholder), income-elasticity per product (Bjelle et al. 2021; Cap et al. 2024 Eq. 1),
or a sufficiency-targeted basket. See docs/backlog.md §Modelling decisions.

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

    TODO: implement — see docs/backlog.md §Sequencing (GitHub issue pending)
    """
    raise NotImplementedError
