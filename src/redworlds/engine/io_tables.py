"""Low-level IO table operations on pymrio.IOSystem objects.

All functions are pure: they receive an IOSystem and return a new (or modified)
IOSystem without mutating the original. Recalculate() is the caller's responsibility
after a series of changes.

References:
  - docs/design/architecture.md — data layer overview
  - pymrio docs: https://pymrio.readthedocs.io
"""

import pymrio


def scale_final_demand(
    mrio: pymrio.IOSystem,
    region: str,
    sector: str,
    factor: float,
) -> pymrio.IOSystem:
    """Scale the final demand of a sector in a region by a multiplicative factor.

    Args:
        mrio: The IO system to modify (a copy is returned; original is not mutated).
        region: EXIOBASE region code (use region_mapping to convert game regions first).
        sector: EXIOBASE sector label.
        factor: Multiplicative scale factor. 0.9 means a 10% reduction.

    Returns:
        Updated IO system with the final demand scaled.

    TODO: implement — see GitHub issue #12
    """
    raise NotImplementedError


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

    TODO: implement — see GitHub issue #13
    """
    raise NotImplementedError


def get_sector_emissions(
    mrio: pymrio.IOSystem,
    region: str,
    sector: str,
) -> float:
    """Extract the total GHG emissions for a sector and region.

    Requires the IO system to have been calculated (mrio.calc_all()).

    Args:
        mrio: A calculated IO system with emissions satellite accounts.
        region: EXIOBASE region code.
        sector: EXIOBASE sector label.

    Returns:
        Total GHG emissions in the satellite account's units (typically kt CO2-eq).

    TODO: implement — see GitHub issue #14
    """
    raise NotImplementedError
