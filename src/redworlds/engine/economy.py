"""The economy-size step of the baseline walk: grow each region's final demand.

In an input-output table a region's GDP equals its final demand, so the size of each
economy is something the walk *sets*; nothing in the model forecasts it. This step scales
everything a region's final consumers buy — households, government, investment — by one
factor, normally the ratio of the region's real GDP in the target year to its GDP in the
base year.

On its own this step says: the world of the target year is the base year's world, bigger.
Every recipe, every emission rate and every household basket is unchanged. That is
deliberately too simple. Run alone it overshoots observed emissions, and the size of the
overshoot is the amount the other steps of the walk have to explain.

Nothing here re-solves the system; call ``engine.io_tables.recalculate_from_final_demand``
afterwards (or the coefficient path, if a recipe step was applied as well).

References:
  - docs/design/baseline_walk.md — the walk this is step 1 of
  - docs/design/assumptions.md — "The baseline walk: economy size"
"""

from collections.abc import Mapping

import pymrio


def scale_economies(mrio: pymrio.IOSystem, factors: Mapping[str, float]) -> pymrio.IOSystem:
    """Return a copy of ``mrio`` with each region's final demand scaled by its factor.

    Args:
        mrio: The IO system to change. Not mutated.
        factors: {consuming region: multiplicative factor}. 1.5 means final demand half as
            large again. Regions absent from the mapping are left alone.

    Returns:
        An uncalculated copy with only ``Y`` changed.

    Raises:
        ValueError: If a factor is negative or a region is not in the table.
    """
    if mrio.Y is None:
        raise ValueError("scale_economies needs a system with Y")
    regions = set(mrio.get_regions())
    unknown = sorted(set(factors) - regions)
    if unknown:
        raise ValueError(f"regions not in the table: {unknown}")
    negative = sorted(region for region, factor in factors.items() if factor < 0.0)
    if negative:
        raise ValueError(f"factors must be non-negative; got negative values for {negative}")

    result = mrio.copy()
    assert result.Y is not None
    for region, factor in factors.items():
        columns = (region, slice(None))
        result.Y.loc[:, columns] = result.Y.loc[:, columns] * factor
    return result
