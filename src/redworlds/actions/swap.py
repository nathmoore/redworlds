"""Consumer-side SWAP: replace a service and re-spend the money left over.

SWAP keeps the household budget closed. Demand for the source basket falls; the removed
spend is converted to physical energy using the source products' EXIOBASE prices; and the
replacement service is converted back to money using the household electricity mix. Any
remainder is spread proportionally across the household basket as deliberate rebound.

Fuel tapes can also make the relevant share of direct household emissions (``F_Y``) follow
the source fuel's own change, using the same correction as REDUCE.
"""

from collections.abc import Mapping, Sequence

import pandas as pd
import pymrio

from redworlds.engine.balancing import rebalance_economy
from redworlds.engine.io_tables import HOUSEHOLDS, recalculate_from_final_demand, scale_direct_emissions

ENERGY_EXTENSION: str = "satellite"
ENERGY_STRESSOR: str = "Energy Carrier Supply: Total"


def _energy_bought(
    mrio: pymrio.IOSystem,
    spend: pd.DataFrame,
    energy_extension: str,
    energy_stressor: str | tuple[str, ...],
) -> float:
    """Convert a producer-by-product spend slice to TJ at each row's basic price."""
    if mrio.x is None:
        raise ValueError("apply_swap needs a calculated system")
    positive = spend.clip(lower=0.0)
    if float(positive.to_numpy().sum()) == 0.0:
        return 0.0
    account = getattr(mrio, energy_extension)
    supply = account.F.loc[energy_stressor].astype(float).reindex(positive.index)
    output = mrio.x["indout"].astype(float).reindex(positive.index)
    active = positive.sum(axis=1) > 0.0
    invalid = active & (supply.isna() | output.isna() | (supply <= 0.0) | (output <= 0.0))
    if invalid.any():
        labels = [f"{region}/{sector}" for region, sector in invalid.index[invalid]]
        raise ValueError(f"cannot price positive final demand with no physical energy supply: {labels}")
    price_per_tj = output / supply
    active_rows = active.index[active]
    return float(positive.loc[active_rows].div(price_per_tj.loc[active_rows], axis="index").to_numpy().sum())


def _add_proportionally(target: pd.DataFrame, amount: float) -> pd.DataFrame:
    """Return a demand slice with ``amount`` distributed over its positive baseline cells."""
    positive = target.clip(lower=0.0)
    total = float(positive.to_numpy().sum())
    if total <= 0.0:
        raise ValueError("replacement demand has no positive baseline household mix")
    return target + positive * (amount / total)


def apply_swap(
    mrio: pymrio.IOSystem,
    region: str,
    from_technology: str | Sequence[str],
    replacement_technology: str | Sequence[str],
    pct_rollout: float,
    service_energy_ratio: float = 1.0,
    categories: Sequence[str] = (HOUSEHOLDS,),
    delivery_sector: str | None = None,
    direct_emissions_extension: str | None = None,
    weights: Mapping[str, float] | None = None,
    direct_emissions_driver: str | None = None,
    direct_emissions_share: float = 1.0,
    energy_extension: str = ENERGY_EXTENSION,
    energy_stressor: str | tuple[str, ...] = ENERGY_STRESSOR,
) -> pymrio.IOSystem:
    """Replace source energy with service-equivalent energy and preserve the budget.

    ``service_energy_ratio`` is physical, not monetary: one third means one TJ of delivered
    electricity replaces three TJ of petrol or mains gas. The function prices both sides
    from the energy extension. Replacement generation follows the region's existing
    household generation mix; its electricity-delivery margin is restored separately at
    the baseline ratio. Rebalancing then re-spends a saving or withdraws an extra cost.

    Args:
        mrio: The calculated baseline. Not mutated; a calculated copy is returned.
        region: Consuming region label.
        from_technology: Source energy product or basket of products.
        replacement_technology: Electricity-generation products supplying the replacement.
        pct_rollout: Fraction of source demand replaced, in [0, 1].
        service_energy_ratio: Replacement TJ per source TJ removed. Must be non-negative.
        categories: Final-demand categories changed; households by default.
        delivery_sector: Optional electricity-delivery product. Its baseline household
            margin per euro of generation is added to the replacement purchase.
        direct_emissions_extension: Account whose selected direct emissions follow the fuel.
        weights: Optional multiplier on rollout for each source product.
        direct_emissions_driver: Source product whose realised cut drives ``F_Y``.
        direct_emissions_share: Share of the selected ``F_Y`` column attributable to that
            driver. The rest is held unchanged.
        energy_extension: Physical-energy satellite account.
        energy_stressor: Energy-supply row, in TJ for EXIOBASE.

    Returns:
        A calculated, closed-budget IO system after the swap and flat re-spend.

    Raises:
        ValueError: If a fraction is invalid or an active energy product cannot be priced.
    """
    if not 0.0 <= pct_rollout <= 1.0:
        raise ValueError(f"pct_rollout must be in [0, 1]; got {pct_rollout}")
    if service_energy_ratio < 0.0:
        raise ValueError(f"service_energy_ratio must be non-negative; got {service_energy_ratio}")
    if not 0.0 <= direct_emissions_share <= 1.0:
        raise ValueError(f"direct_emissions_share must be in [0, 1]; got {direct_emissions_share}")
    if mrio.Y is None:
        raise ValueError("apply_swap needs a calculated system")

    sources = [from_technology] if isinstance(from_technology, str) else list(from_technology)
    replacements = [replacement_technology] if isinstance(replacement_technology, str) else list(replacement_technology)
    factors = {product: 1.0 - pct_rollout * (weights or {}).get(product, 1.0) for product in sources}
    if any(factor < 0.0 for factor in factors.values()):
        raise ValueError("pct_rollout times a product weight cannot exceed 1.0")

    result = mrio.copy()
    assert result.Y is not None
    columns = (region, list(categories))
    source_rows = (slice(None), sources)
    before_source = mrio.Y.loc[source_rows, columns]
    after_source = before_source.copy()
    for product, factor in factors.items():
        after_source.loc[(slice(None), product), :] *= factor
    result.Y.loc[source_rows, columns] = after_source
    removed_source = before_source - after_source
    replacement_energy_tj = _energy_bought(mrio, removed_source, energy_extension, energy_stressor)
    replacement_energy_tj *= service_energy_ratio

    if replacement_energy_tj > 0.0:
        replacement_rows = (slice(None), replacements)
        baseline_generation = mrio.Y.loc[replacement_rows, columns]
        baseline_generation_spend = float(baseline_generation.clip(lower=0.0).to_numpy().sum())
        baseline_generation_energy = _energy_bought(mrio, baseline_generation, energy_extension, energy_stressor)
        if baseline_generation_energy <= 0.0:
            raise ValueError("replacement demand has no positive physical energy supply")
        replacement_spend = replacement_energy_tj * baseline_generation_spend / baseline_generation_energy
        result.Y.loc[replacement_rows, columns] = _add_proportionally(
            result.Y.loc[replacement_rows, columns], replacement_spend
        )

        if delivery_sector is not None:
            delivery_rows = (slice(None), delivery_sector)
            baseline_delivery = mrio.Y.loc[delivery_rows, columns]
            delivery_spend = float(baseline_delivery.clip(lower=0.0).to_numpy().sum())
            margin_ratio = delivery_spend / baseline_generation_spend
            if delivery_spend > 0.0:
                result.Y.loc[delivery_rows, columns] = _add_proportionally(
                    result.Y.loc[delivery_rows, columns], replacement_spend * margin_ratio
                )

    remainder = float(mrio.Y.to_numpy().sum() - result.Y.to_numpy().sum())
    balanced = rebalance_economy(result, region, remainder, categories)

    if direct_emissions_extension is not None:
        if direct_emissions_driver is None:
            realised_cut = pct_rollout
        elif direct_emissions_driver in sources:
            realised_cut = pct_rollout * (weights or {}).get(direct_emissions_driver, 1.0)
        else:
            raise ValueError(
                f"direct_emissions_driver {direct_emissions_driver!r} is not in the source basket {sources}"
            )
        direct_factor = 1.0 - realised_cut * direct_emissions_share
        balanced = scale_direct_emissions(
            balanced,
            region,
            direct_factor,
            direct_emissions_extension,
            categories,
        )

    return recalculate_from_final_demand(balanced)
