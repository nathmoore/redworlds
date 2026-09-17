"""Low-level IO table operations on pymrio.IOSystem objects.

All functions are pure: they receive an IOSystem and return a new IOSystem (or a number)
without mutating the original. Recalculation is the caller's responsibility; see
``recalculate_from_final_demand`` for the cheap Y-side path.

Emissions are read on a consumption basis (pymrio's ``D_cba``): a region is charged for
everything its final demand pulls into production, wherever in the world that production
happens. This is what the game's contract asks for: a REDUCE tape in Europe that cuts
demand for imported electronics is credited with the abatement in the factories abroad.
Production-based figures would silently make every such tape look smaller.

References:
  - docs/design/red_carbon_contract.md §5 — consumption-based accounting credits imports
  - docs/design/architecture.md — data layer overview
  - pymrio docs: https://pymrio.readthedocs.io
"""

from collections.abc import Sequence

import pandas as pd
import pymrio

# EXIOBASE-specific: the extension and impact row that hold total GHG in kg CO2-eq.
# pymrio's test world instead has an ``emissions`` extension with rows like
# ("emission_type1", "air"); pass those explicitly in tests.
GHG_EXTENSION: str = "impacts"
GHG_STRESSOR: str = "GHG emissions (GWP100) | Problem oriented approach: baseline (CML, 2001) | GWP100 (IPCC, 2007)"

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
    result = mrio.copy()
    assert result.Y is not None
    sectors = [sector] if isinstance(sector, str) else list(sector)
    columns = (region, list(categories)) if categories is not None else (region, slice(None))
    rows = (slice(None), sectors)
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


def shift_sector_share(
    mrio: pymrio.IOSystem,
    region: str,
    from_sector: str,
    to_sector: str,
    fraction: float,
) -> pymrio.IOSystem:
    """Shift a fraction of one sector's IO flows to another sector in the same region.

    Used by SWAP actions to move demand from one technology to another.

    Args:
        mrio: The IO system to modify (a copy is returned; original is not mutated).
        region: EXIOBASE region code.
        from_sector: Sector losing share.
        to_sector: Sector gaining share.
        fraction: Fraction of ``from_sector`` flows to shift, in [0.0, 1.0].

    Returns:
        Updated IO system with sector shares adjusted.

    TODO: implement — see docs/backlog.md §Sequencing (GitHub issue pending)
    """
    raise NotImplementedError


def _stressor_row(frame: pd.DataFrame, stressor: str | tuple[str, ...]) -> pd.Series:
    """Select one stressor's row from a pymrio account table, whatever the index depth."""
    return frame.loc[stressor]


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
