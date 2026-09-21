"""Low-level IO table operations on pymrio.IOSystem objects.

All functions are pure: they receive an IOSystem and return a new IOSystem (or a number)
without mutating the original. Recalculation is the caller's responsibility; see
``recalculate_from_final_demand`` for the cheap Y-side path.

Emissions are read on a consumption basis (pymrio's ``D_cba``): a region is charged for
everything its final demand pulls into production, wherever in the world that production
happens. This is what the game's contract asks for: a REDUCE tape in Europe that cuts
demand for imported electronics is credited with the abatement in the factories abroad.
Production-based figures would silently make every such tape look smaller.

Direct household emissions (``F_Y`` — fuel burnt in cars and boilers rather than bought
embodied in a product) are the one account that does not follow from the product rows.
pymrio rebuilds them from a per-column coefficient on every recalculation, so a tape that
wants them to move with one product rather than with total spend has to say so:
see ``scale_direct_emissions``.

References:
  - docs/design/red_carbon_contract.md §5 — consumption-based accounting credits imports
  - docs/design/architecture.md — data layer overview
  - pymrio docs: https://pymrio.readthedocs.io
"""

from collections.abc import Mapping, Sequence

import pandas as pd
import pymrio

# EXIOBASE-specific: the extension and impact row that hold total GHG in kg CO2-eq.
# pymrio's test world instead has an ``emissions`` extension with rows like
# ("emission_type1", "air"); pass those explicitly in tests.
GHG_EXTENSION: str = "impacts"
GHG_STRESSOR: str = "GHG emissions (GWP100) | Problem oriented approach: baseline (CML, 2001) | GWP100 (IPCC, 2007)"
CO2_STRESSOR: str = (
    "Carbon dioxide (CO2) IPCC categories 1 to 4 and 6 to 7 (excl land use, land use change and forestry)"
)

_TONNES_PER_UNIT: dict[str, float] = {
    "kg": 1e-3,
    "kg CO2 eq.": 1e-3,
    "kg CO2-eq": 1e-3,
    "Gg": 1e3,
    "Gg CO2-eq": 1e3,
}

# EXIOBASE-specific final demand categories. Households, NPISH and government together
# are the "non-capital" demand a REDUCE tape may cut; GFCF is BUILD's currency and is
# never touched by REDUCE (docs/design/red_carbon_contract.md §5).
HOUSEHOLDS: str = "Final consumption expenditure by households"
NPISH: str = "Final consumption expenditure by non-profit organisations serving households (NPISH)"
GOVERNMENT: str = "Final consumption expenditure by government"
GFCF: str = "Gross fixed capital formation"
CONSUMPTION_CATEGORIES: tuple[str, ...] = (HOUSEHOLDS, NPISH, GOVERNMENT)


def scale_final_demand(
    mrio: pymrio.IOSystem,
    region: str,
    sector: str | Sequence[str],
    factor: float,
    categories: Sequence[str] | None = None,
) -> pymrio.IOSystem:
    """Scale a region's final demand for one or more products by a multiplicative factor.

    ``region`` is the *consuming* region: the Y column. The scaled rows cover the product
    from every producing region, so imports of the product are scaled along with domestic
    supply. That is what "Europe buys 10% fewer computers" means in an MRIO table.

    Args:
        mrio: The IO system to modify. Not mutated; a copy is returned.
        region: Region code of the consumer (an EXIOBASE code, or a game region after
            ``aggregate_regions``).
        sector: One product label, or a basket of them.
        factor: Multiplicative scale factor. 0.9 means a 10% reduction.
        categories: Final demand categories (Y column labels) to scale. Defaults to all
            categories in the region's column block. REDUCE passes
            ``CONSUMPTION_CATEGORIES`` so investment is left alone.

    Returns:
        A copy of ``mrio`` with only ``Y`` changed. Call ``recalculate_from_final_demand``
        before reading emissions from it.
    """
    sectors = [sector] if isinstance(sector, str) else list(sector)
    return scale_final_demand_per_product(mrio, region, dict.fromkeys(sectors, factor), categories)


def scale_final_demand_per_product(
    mrio: pymrio.IOSystem,
    region: str,
    factors: Mapping[str, float],
    categories: Sequence[str] | None = None,
) -> pymrio.IOSystem:
    """Scale a region's final demand product by product, each with its own factor.

    The general form of :func:`scale_final_demand`, which is the same operation with one
    factor repeated. A basket needs this when its products do not respond equally: extending
    the life of a laptop removes a quarter of its replacement demand, extending the life of a
    washing machine removes a twelfth, and cutting both by the same percentage would describe
    neither.

    Each product is still scaled across every producing region, so imports move with domestic
    supply.

    Args:
        mrio: The IO system to modify. Not mutated; a copy is returned.
        region: Region code of the consumer.
        factors: {product label: multiplicative factor}. 0.9 means a 10% reduction in that
            product. Products absent from the mapping are left alone.
        categories: Final demand categories (Y column labels) to scale. Defaults to all
            categories in the region's column block.

    Returns:
        A copy of ``mrio`` with only ``Y`` changed. Call ``recalculate_from_final_demand``
        before reading emissions from it.
    """
    result = mrio.copy()
    assert result.Y is not None
    columns = (region, list(categories)) if categories is not None else (region, slice(None))
    # One .loc assignment per distinct factor rather than per product: a 200-product basket
    # with three distinct rates is three assignments, not two hundred.
    by_factor: dict[float, list[str]] = {}
    for product, factor in factors.items():
        by_factor.setdefault(factor, []).append(product)
    for factor, products in by_factor.items():
        rows = (slice(None), products)
        result.Y.loc[rows, columns] = result.Y.loc[rows, columns] * factor
    return result


def recalculate_from_final_demand(mrio: pymrio.IOSystem) -> pymrio.IOSystem:
    """Recalculate a system whose only change since ``calc_all()`` is to ``Y``.

    Keeps the coefficient matrices (A, the Leontief inverse L, the stressor
    intensities S) and recomputes the flows from them: x = L·y, then the satellite
    accounts. On EXIOBASE this is one matrix-vector product rather than a matrix
    inversion, which is why Y-side tapes are the MVP path
    (docs/design/assumptions.md, "Recalculation cost").

    Args:
        mrio: A calculated system with a modified ``Y``. Not mutated; a copy is returned.

    Returns:
        A fully calculated copy.
    """
    result = mrio.copy()
    final_demand = result.Y
    result.reset_all_to_coefficients()  # keeps A, L, S; drops every flow table, Y included
    result.Y = final_demand
    result.calc_all()
    return result


def recalculate_from_technical_coefficients(mrio: pymrio.IOSystem) -> pymrio.IOSystem:
    """Recalculate a system whose ``A`` coefficients and possibly ``Y`` have changed.

    Keeps the stressor intensities (``S`` and ``S_Y``), invalidates the old Leontief
    inverse, and rebuilds every flow account. This is the expensive path used by BUILD's
    operating phase.

    Args:
        mrio: A calculated system carrying the changed ``A`` and ``Y``. Not mutated.

    Returns:
        A fully calculated copy with a new Leontief inverse.
    """
    result = mrio.copy()
    coefficients = result.A
    final_demand = result.Y
    result.reset_all_to_coefficients()
    result.A = coefficients
    result.L = None
    result.Y = final_demand
    result.calc_all()
    return result


def scale_direct_emissions(
    mrio: pymrio.IOSystem,
    region: str,
    factor: float,
    extension: str = GHG_EXTENSION,
    categories: Sequence[str] | None = None,
) -> pymrio.IOSystem:
    """Scale a region's direct household emissions (``F_Y``) by an explicit factor.

    ``F_Y`` is the fuel people burn themselves — petrol in cars, gas in boilers. It is
    not attributable to any product row, so pymrio carries it as a coefficient ``S_Y``
    normalised per final demand *column* total. Left alone, that means a tape which cuts
    one product drags direct emissions down by the change in the household's **whole**
    shopping basket. For a broad basket that is right: cut 5% of everything and the fuel
    falls 5% too. For a fuel tape it is wrong, and badly so — ``F_Y`` is 11% of the world
    total (5.1 of 44.5 Gt CO2e). A tape that bans household gas should move ``F_Y`` by the
    change in gas, not by the change in total spend.

    This function lets the caller say so. Only the tape knows which product drives the
    fuel, so the factor is passed in rather than inferred. One important limit: EXIOBASE's
    characterised ``F_Y`` is resolved by region and final-demand category, not by purchased
    fuel. The factor therefore scales the whole selected household direct-emissions column.
    At a large gas rollout that also moves petrol combustion; fuel-share apportionment is a
    documented backlog item and the current gas result is an upper bound.

    **Order matters.** Call this *after* ``scale_final_demand`` and *before*
    ``recalculate_from_final_demand``. The recalculation throws ``F_Y`` away and rebuilds
    it from ``S_Y``, so the fix only survives if it is written into ``S_Y`` as well — and
    ``S_Y`` is only meaningful against the final demand that is in the system right now.
    Call this before the demand cut and the cut will re-apply the column-total ride on top.

    Args:
        mrio: The IO system to modify, with its final demand already cut. Not mutated;
            a copy is returned.
        region: Region code of the consumer whose direct emissions move.
        factor: Multiplicative scale factor — the driving product's own change. 0.9 means
            the fuel's demand fell 10%, so its direct emissions fall 10%.
        extension: Name of the satellite account. EXIOBASE: ``"impacts"``.
        categories: Final demand categories (``F_Y`` column labels) to scale. Defaults to
            every category in the region's column block. Pass the same categories the
            demand cut used, so the emissions that move are the ones whose spend moved.

    Returns:
        A copy of ``mrio`` whose ``F_Y`` and ``S_Y`` both carry the new figure and agree
        with each other. Call ``recalculate_from_final_demand`` next.
    """
    result = mrio.copy()
    account = getattr(result, extension)
    columns = (region, list(categories)) if categories is not None else (region, slice(None))
    # pymrio's test world stores F_Y as int64, which refuses a scaled float in place.
    direct = account.F_Y.astype(float)
    direct.loc[:, columns] = direct.loc[:, columns] * factor
    account.F_Y = direct
    account.S_Y = pymrio.calc_S_Y(direct, result.Y.sum(axis=0))
    return result


def shift_sector_share(
    mrio: pymrio.IOSystem,
    region: str,
    from_sector: str | Sequence[str],
    to_sector: str,
    fraction: float,
    categories: Sequence[str] = (HOUSEHOLDS,),
    replacement_ratio: float = 1.0,
    weights: Mapping[str, float] | None = None,
) -> pymrio.IOSystem:
    """Move consumer demand from products to a replacement product.

    The source products are cut across all producing regions. ``replacement_ratio`` is a
    purely monetary multiplier. It must not be used for a physical efficiency such as heat-
    pump COP or EV energy use; :func:`redworlds.actions.swap.apply_swap` prices those from
    the energy account. Any remainder is deliberately left unspent here for balancing.

    Args:
        mrio: The IO system to modify (a copy is returned; original is not mutated).
        region: EXIOBASE region code.
        from_sector: One product, or a basket of products, losing share.
        to_sector: Sector gaining share.
        fraction: Fraction of ``from_sector`` flows to shift, in [0.0, 1.0].
        categories: Final-demand categories to change.
        replacement_ratio: Replacement spend per unit of source spend removed.
        weights: Optional multiplier on ``fraction`` for each source product.

    Returns:
        A copy with ``Y`` adjusted but not recalculated or rebalanced.

    Raises:
        ValueError: If the fraction is outside [0, 1] or the monetary ratio is negative.
    """
    if not 0.0 <= fraction <= 1.0:
        raise ValueError(f"fraction must be in [0, 1]; got {fraction}")
    if replacement_ratio < 0.0:
        raise ValueError(f"replacement_ratio must be non-negative; got {replacement_ratio}")

    sources = [from_sector] if isinstance(from_sector, str) else list(from_sector)
    factors = {sector: 1.0 - fraction * (weights or {}).get(sector, 1.0) for sector in sources}
    if any(factor < 0.0 for factor in factors.values()):
        raise ValueError("fraction times a product weight cannot exceed 1.0")
    result = scale_final_demand_per_product(mrio, region, factors, categories)
    assert mrio.Y is not None and result.Y is not None
    columns = (region, list(categories))
    source_rows = (slice(None), sources)
    removed = float((mrio.Y.loc[source_rows, columns] - result.Y.loc[source_rows, columns]).to_numpy().sum())
    replacement = removed * replacement_ratio
    if replacement == 0.0:
        return result

    target_rows = (slice(None), to_sector)
    target = result.Y.loc[target_rows, columns].clip(lower=0.0)
    target_total = float(target.to_numpy().sum())
    if target_total > 0.0:
        result.Y.loc[target_rows, columns] = result.Y.loc[target_rows, columns] + target * (replacement / target_total)
    else:
        result.Y.loc[(region, to_sector), (region, categories[0])] += replacement
    return result


def _stressor_row(frame: pd.DataFrame, stressor: str | tuple[str, ...]) -> pd.Series:
    """Select one stressor's row from a pymrio account table, whatever the index depth."""
    return frame.loc[stressor]


def emissions_to_tonnes(
    mrio: pymrio.IOSystem,
    value: float,
    extension: str = GHG_EXTENSION,
    stressor: str | tuple[str, ...] = GHG_STRESSOR,
) -> float:
    """Convert one emissions value to tonnes using its extension's declared unit.

    EXIOBASE's headline GHG row is kg while its CO2-only row is Gg, a factor of one
    million between their tonne conversions. Reading the unit table here prevents a caller
    from silently applying one row's conversion to the other.
    """
    account = getattr(mrio, extension)
    unit = str(account.unit.loc[stressor, "unit"])
    try:
        factor = _TONNES_PER_UNIT[unit]
    except KeyError as exc:
        raise ValueError(f"unsupported emissions unit {unit!r} for {extension}/{stressor}") from exc
    return value * factor


def get_region_emissions(
    mrio: pymrio.IOSystem,
    region: str,
    extension: str = GHG_EXTENSION,
    stressor: str | tuple[str, ...] = GHG_STRESSOR,
) -> float:
    """Consumption-based GHG footprint of a region, in the extension's units.

    Reads pymrio's ``D_cba_reg``: everything the region's final demand pulls into
    production anywhere in the world, plus the region's direct household emissions
    (``F_Y``, e.g. fuel burnt in cars and boilers). Requires a calculated system.

    Args:
        mrio: A calculated IO system.
        region: Region code (EXIOBASE code, or a game region after ``aggregate_regions``).
        extension: Name of the satellite account. EXIOBASE: ``"impacts"``.
        stressor: Row label within the account. A tuple for multi-level indices, as in
            pymrio's test world.

    Returns:
        Annual footprint as a float (kg CO2-eq for EXIOBASE).
    """
    account = getattr(mrio, extension)
    return float(_stressor_row(account.D_cba_reg, stressor)[region])


def get_sector_emissions(
    mrio: pymrio.IOSystem,
    region: str,
    sector: str,
    extension: str = GHG_EXTENSION,
    stressor: str | tuple[str, ...] = GHG_STRESSOR,
) -> float:
    """Consumption-based GHG emissions embodied in a region's final demand for one product.

    Reads pymrio's ``D_cba``, so the number covers the whole supply chain behind the
    product, wherever it runs. Direct household emissions (``F_Y``) are not included:
    they are not attributable to a product row. Requires a calculated system.

    Args:
        mrio: A calculated IO system with the named extension.
        region: Consuming region code.
        sector: Product label.
        extension: Name of the satellite account. EXIOBASE: ``"impacts"``.
        stressor: Row label within the account.

    Returns:
        Annual embodied emissions as a float (kg CO2-eq for EXIOBASE).
    """
    account = getattr(mrio, extension)
    return float(_stressor_row(account.D_cba, stressor)[(region, sector)])
