"""The spending-mix step of the baseline walk: what households buy as incomes change.

The economy-size step makes every household basket bigger without changing its shape. In
fact the shape moves with income: a richer household spends a smaller share on food and a
larger share on travel, eating out and communication. This step moves the shares and leaves
the total alone, so that size has one home (``engine/economy.py``) and mix has another.

The method is that of Cap et al. 2024 (their Eq. 1), using income elasticities estimated on
EXIOBASE by Bjelle et al. 2021. For each product ``i``::

    spending_i  →  spending_i × (1 + elasticity_i × income_change)

and the basket is then rescaled to its original total. With an elasticity of one for every
product the step does nothing.

Simplifications, all recorded in docs/design/assumptions.md:

- An elasticity is held at its 2011 value however far income moves.
- There are no prices: nothing here responds to a product becoming cheaper or dearer.
- Only the household column moves. Government and investment keep their 2011 mix.
- Fuel households burn themselves (``F_Y``) follows total household spending, which this
  step does not change, and not the share of it spent on fuel.

Nothing here re-solves the system; call ``engine.io_tables.recalculate_from_final_demand``
afterwards (or the coefficient path, if a recipe step was applied as well).

References:
  - docs/design/baseline_walk.md — the walk this is step 2 of
  - docs/design/how_we_predict_the_future.md — what goes in, and what is assumed
"""

from collections.abc import Mapping, Sequence

import pymrio

from redworlds.engine.io_tables import HOUSEHOLDS


def spending_factors(elasticities: Mapping[str, float], income_change: float) -> dict[str, float]:
    """Return each product's growth relative to income: ``1 + elasticity × income_change``.

    Args:
        elasticities: {product: income elasticity of household spending}.
        income_change: Relative change in income per head. 0.5 means half as large again.

    Raises:
        ValueError: If a factor would be negative, which a large fall in income combined
            with an elasticity above one can produce.
    """
    factors = {product: 1.0 + elasticity * income_change for product, elasticity in elasticities.items()}
    negative = sorted(product for product, factor in factors.items() if factor < 0.0)
    if negative:
        raise ValueError(f"income change {income_change:g} drives spending below zero for {negative}")
    return factors


def shift_spending_mix(
    mrio: pymrio.IOSystem,
    region: str,
    elasticities: Mapping[str, float],
    income_change: float,
    categories: Sequence[str] = (HOUSEHOLDS,),
) -> pymrio.IOSystem:
    """Move a region's household basket toward what a different income buys, total unchanged.

    Args:
        mrio: The IO system to change. Not mutated.
        region: The consuming region.
        elasticities: {product: income elasticity}. A product absent from the mapping is
            treated as having an elasticity of one: its spending follows income.
        income_change: Relative change in the region's income per head since the year the
            basket describes. 0.5 means half as large again; 0.0 leaves the basket alone.
        categories: Final-demand columns to change; households by default.

    Returns:
        An uncalculated copy with only ``Y`` changed, and the region's total spending in
        ``categories`` exactly as it was.

    Raises:
        ValueError: If a product would be driven below zero, or the basket is empty.
    """
    if mrio.Y is None:
        raise ValueError("shift_spending_mix needs a system with Y")
    result = mrio.copy()
    assert result.Y is not None
    columns = (region, list(categories))
    basket = result.Y.loc[:, columns].astype(float)
    total_before = float(basket.to_numpy().sum())
    if total_before <= 0.0:
        raise ValueError(f"cannot shift the spending mix of {region!r}: the selected basket is empty")

    factors = spending_factors(elasticities, income_change)
    product_of_row = basket.index.get_level_values(1)
    # The share that follows income (elasticity one) is the default for unlisted products.
    row_factor = [factors.get(product, 1.0 + income_change) for product in product_of_row]
    shifted = basket.mul(row_factor, axis="index")
    result.Y.loc[:, columns] = shifted * (total_before / float(shifted.to_numpy().sum()))
    return result
