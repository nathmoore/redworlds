"""Consumer-side SWAP: replace a service and re-spend the money left over.

SWAP keeps the household budget closed. Demand for the source basket falls, demand for
the replacement product rises by the service-equivalent spend, and the remainder is spread
proportionally across the household basket. This deliberate re-spend is SWAP's rebound.

Fuel tapes can also make direct household emissions (``F_Y``) follow the source fuel's own
change, using the same correction as REDUCE. See :mod:`redworlds.actions.reduce`.
"""

from collections.abc import Mapping, Sequence

import pymrio

from redworlds.engine.balancing import rebalance_economy
from redworlds.engine.io_tables import (
    HOUSEHOLDS,
    recalculate_from_final_demand,
    scale_direct_emissions,
    shift_sector_share,
)


def apply_swap(
    mrio: pymrio.IOSystem,
    region: str,
    from_technology: str | Sequence[str],
    to_technology: str,
    pct_rollout: float,
    replacement_ratio: float = 1.0,
    categories: Sequence[str] = (HOUSEHOLDS,),
    direct_emissions_extension: str | None = None,
    weights: Mapping[str, float] | None = None,
    direct_emissions_driver: str | None = None,
) -> pymrio.IOSystem:
    """Replace household demand while preserving total final demand.

    Args:
        mrio: The calculated baseline. Not mutated; a calculated copy is returned.
        region: Consuming region label.
        from_technology: Source product or basket of products.
        to_technology: Replacement product. Beta Day uses retail electricity.
        pct_rollout: Fraction of source demand replaced, in [0, 1].
        replacement_ratio: Replacement spend per unit of source spend removed. A value of
            one third represents either heat-pump heat at COP 3 or EV travel using roughly
            one third of petrol/diesel energy.
        categories: Final-demand categories changed; households by default.
        direct_emissions_extension: Satellite account whose direct household emissions
            follow the source fuel's change. Leave ``None`` for non-combustion swaps.
        weights: Optional multiplier on rollout for each source product.
        direct_emissions_driver: Source product whose realised cut drives ``F_Y``. Required
            for a weighted basket if direct emissions are enabled.

    Returns:
        A calculated, closed-budget IO system after the swap and flat re-spend.

    Raises:
        ValueError: If ``pct_rollout`` or ``replacement_ratio`` is outside [0, 1].
    """
    if not 0.0 <= pct_rollout <= 1.0:
        raise ValueError(f"pct_rollout must be in [0, 1]; got {pct_rollout}")

    shifted = shift_sector_share(
        mrio,
        region,
        from_technology,
        to_technology,
        pct_rollout,
        categories,
        replacement_ratio,
        weights,
    )
    assert mrio.Y is not None and shifted.Y is not None
    remainder = float(mrio.Y.to_numpy().sum() - shifted.Y.to_numpy().sum())
    balanced = rebalance_economy(shifted, region, remainder, categories)

    if direct_emissions_extension is not None:
        sources = [from_technology] if isinstance(from_technology, str) else list(from_technology)
        if direct_emissions_driver is None:
            direct_factor = 1.0 - pct_rollout
        elif direct_emissions_driver in sources:
            direct_factor = 1.0 - pct_rollout * (weights or {}).get(direct_emissions_driver, 1.0)
        else:
            raise ValueError(
                f"direct_emissions_driver {direct_emissions_driver!r} is not in the source basket {sources}"
            )
        balanced = scale_direct_emissions(
            balanced,
            region,
            direct_factor,
            direct_emissions_extension,
            categories,
        )

    return recalculate_from_final_demand(balanced)
