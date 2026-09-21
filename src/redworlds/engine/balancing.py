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

from collections.abc import Sequence

import pymrio

from redworlds.engine.io_tables import HOUSEHOLDS


def rebalance_economy(
    mrio: pymrio.IOSystem,
    changed_region: str,
    amount: float,
    categories: Sequence[str] = (HOUSEHOLDS,),
    excluded_sectors: Sequence[str] = (),
) -> pymrio.IOSystem:
    """Re-spend or withdraw money proportionally across a region's final demand.

    This is the deliberately simple ``flat proportional`` rung in the rebalancing design:
    every eligible final-demand cell keeps its current share of the basket. A positive
    ``amount`` is re-spent; a negative one crowds out existing demand. The latter is exposed
    for BUILD's reallocation cross-check, although Beta Day BUILD uses injection instead.

    Called by SWAP for the money left after buying the replacement service, and optionally
    by BUILD. REDUCE never calls it.

    Args:
        mrio: The IO system after a sector change (a copy is returned).
        changed_region: The region where the change was applied.
        amount: Total money to add (positive) or withdraw (negative), in the table's unit.
        categories: Final-demand columns across which to spread the amount.
        excluded_sectors: Products which must not receive any of the re-spend. BUILD uses
            this to avoid immediately crowding out the four products it just injected.

    Returns:
        A copy with exactly ``amount`` distributed across the eligible cells.

    Raises:
        ValueError: If the selected basket has no positive demand, or a withdrawal is larger
            than that basket.
    """
    result = mrio.copy()
    assert result.Y is not None

    columns = (changed_region, list(categories))
    eligible = result.Y.loc[:, columns].astype(float).copy()
    if excluded_sectors:
        eligible.loc[(slice(None), list(excluded_sectors)), :] = 0.0
    eligible = eligible.clip(lower=0.0)
    basket_total = float(eligible.to_numpy().sum())
    if basket_total <= 0.0:
        raise ValueError(f"cannot rebalance {changed_region!r}: selected final-demand basket is empty")
    if amount < -basket_total:
        raise ValueError(
            f"cannot withdraw {-amount:g} from {changed_region!r}: selected basket contains only {basket_total:g}"
        )

    allocation = eligible * (amount / basket_total)
    result.Y.loc[:, columns] = result.Y.loc[:, columns] + allocation

    # Remove the last few ulps from proportional arithmetic. The closed-budget identity is
    # a contract, not an approximate modelling result, so make it exact at the matrix edge.
    distributed = float(allocation.to_numpy().sum())
    residual = amount - distributed
    if residual:
        flat_position = int(eligible.to_numpy().argmax())
        row_position, column_position = divmod(flat_position, eligible.shape[1])
        row = eligible.index[row_position]
        column = eligible.columns[column_position]
        result.Y.loc[row, column] += residual

    return result
