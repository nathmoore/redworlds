"""Economic rebalancing to maintain a closed IO economy after a player action.

After a SWAP (and a BUILD under the reallocation flag), money not spent on the
displaced product is re-spent elsewhere so total final demand is preserved. REDUCE
actions deliberately do NOT call these functions: the spend leaves the model
(docs/design/assumptions.md, confirmed 2026-09-16).

The weighting that decides where re-spent money goes is one argument, ``weights``:

- **Flat proportional** (no weights): every product keeps its share of the basket, as if
  the household simply bought a little more of everything.
- **Income elasticity** (weights = each product's income elasticity; Bjelle et al. 2021):
  the money goes where an extra euro of income goes. A product's share of the re-spend is
  its budget share times its elasticity, which is its *marginal* budget share: little of a
  windfall is spent on food, more on travel and eating out.
- **Sufficiency-targeted** (weights chosen by a designer): not built. See docs/backlog.md
  §Modelling decisions.

All functions are pure: they receive an IOSystem and return an updated one
without mutating the original.

References:
  - docs/design/assumptions.md — rebalancing approach and post-growth rationale
  - docs/design/game_mechanics.md — which actions trigger rebalancing
"""

from collections.abc import Mapping, Sequence

import pymrio

from redworlds.engine.io_tables import HOUSEHOLDS


def rebalance_economy(
    mrio: pymrio.IOSystem,
    changed_region: str,
    amount: float,
    categories: Sequence[str] = (HOUSEHOLDS,),
    excluded_sectors: Sequence[str] = (),
    weights: Mapping[str, float] | None = None,
) -> pymrio.IOSystem:
    """Re-spend or withdraw money across a region's final demand.

    Without ``weights`` this is the ``flat proportional`` rung: every eligible final-demand
    cell keeps its current share of the basket. With them, each cell's share is multiplied
    by its product's weight first, so the money follows marginal and not average spending.
    A positive ``amount`` is re-spent; a negative one crowds out existing demand. The latter
    is exposed for BUILD's reallocation cross-check, although Beta Day BUILD uses injection.

    Called by SWAP for the money left after buying the replacement service, and optionally
    by BUILD. REDUCE never calls it.

    Args:
        mrio: The IO system after a sector change (a copy is returned).
        changed_region: The region where the change was applied.
        amount: Total money to add (positive) or withdraw (negative), in the table's unit.
        categories: Final-demand columns across which to spread the amount.
        excluded_sectors: Products which must not receive any of the re-spend. BUILD uses
            this to avoid immediately crowding out the four products it just injected.
        weights: {product: weight on its share of the basket}, normally income
            elasticities. A product absent from the mapping has weight one. Omit for
            flat proportional.

    Returns:
        A copy with exactly ``amount`` distributed across the eligible cells.

    Raises:
        ValueError: If the selected basket has no positive demand, a withdrawal is larger
            than that basket, a weight is negative, or a weighted withdrawal would take
            more from a product than is spent on it.
    """
    if weights is not None and any(weight < 0.0 for weight in weights.values()):
        raise ValueError("re-spend weights must be non-negative")
    result = mrio.copy()
    assert result.Y is not None

    columns = (changed_region, list(categories))
    eligible = result.Y.loc[:, columns].astype(float).copy()
    if excluded_sectors:
        eligible.loc[(slice(None), list(excluded_sectors)), :] = 0.0
    eligible = eligible.clip(lower=0.0)
    spent = eligible
    if weights is not None:
        row_weight = [weights.get(product, 1.0) for product in eligible.index.get_level_values(1)]
        eligible = eligible.mul(row_weight, axis="index")
    basket_total = float(eligible.to_numpy().sum())
    spent_total = float(spent.to_numpy().sum())
    if basket_total <= 0.0:
        raise ValueError(f"cannot rebalance {changed_region!r}: selected final-demand basket is empty")
    if amount < -spent_total:
        raise ValueError(
            f"cannot withdraw {-amount:g} from {changed_region!r}: selected basket contains only {spent_total:g}"
        )

    allocation = eligible * (amount / basket_total)
    if bool((spent + allocation < -1e-9 * spent_total).to_numpy().any()):
        raise ValueError(f"weighted withdrawal of {-amount:g} from {changed_region!r} exceeds spending on a product")
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
