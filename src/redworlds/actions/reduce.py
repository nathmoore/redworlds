"""REDUCE action: consume less of a basket of products, with no economic rebalancing.

The tape names a basket of products and a consuming region; the game's outcome fraction
times the tape's ``max_reducible_fraction`` gives ``pct_reduction``.

Red Worlds then:
1. Scales the basket's final demand in the region's consumption columns (households,
   NPISH, government) by ``1 − pct_reduction``. Investment (GFCF) is never touched: that
   is BUILD's currency.
2. Does NOT rebalance the rest of the economy. The spend leaves the model, the economy
   shrinks in proportion, and ``engine.scoring.gdp_impact`` books the difference.
3. Re-solves output and emissions on the cheap Y-side path (the Leontief inverse is
   reused), so the returned system is ready for scoring.

Fuel tapes get one extra step. Direct household emissions — the petrol and gas people
burn themselves, rather than buy embodied in something — belong to no product row, so by
default they follow the size of the household's whole shopping basket. Cut 5% of
everything and they fall 5%, which is right. But a tape that cuts vehicle fuel or bans
household gas is cutting the fuel itself, and those emissions should fall by the change
in the fuel, not by the change in total spend. Such a tape passes
``direct_emissions_extension`` and gets that behaviour; every other tape is untouched.

This is a deliberate post-growth design choice (confirmed 2026-09-16): reduced consumption
is not redirected elsewhere and takes no rebound haircut. Emissions are credited on a
consumption basis, so a European cut in imported electronics is credited with the
abatement in the factories abroad. See docs/design/assumptions.md for the rationale.

References:
  - docs/design/red_carbon_contract.md §3 (rule RE2) and §5 (basket design)
  - docs/design/assumptions.md — post-growth rebalancing assumption
  - data/concordances/exiobase_to_scenario.csv — scenario keys → product baskets (to populate)
"""

from collections.abc import Sequence

import pymrio

from redworlds.engine.io_tables import (
    CONSUMPTION_CATEGORIES,
    recalculate_from_final_demand,
    scale_direct_emissions,
    scale_final_demand,
)


def apply_reduce(
    mrio: pymrio.IOSystem,
    region: str,
    sector: str | Sequence[str],
    pct_reduction: float,
    categories: Sequence[str] = CONSUMPTION_CATEGORIES,
    direct_emissions_extension: str | None = None,
) -> pymrio.IOSystem:
    """Apply a REDUCE action: cut a region's demand for a basket of products, no rebalancing.

    Args:
        mrio: The calculated baseline world. Not mutated; a calculated copy is returned.
        region: Consuming region label as it appears in ``mrio.Y`` (an EXIOBASE code, or a
            game region name after ``aggregate_regions``).
        sector: One product label or a basket of them. Translating a tape's scenario key
            into product labels is the job layer's task, not this function's.
        pct_reduction: Fraction of the basket's demand removed, at most 1.0. A negative
            value is a backfire (the game's outcome fraction can go below zero for REDUCE):
            demand rises instead.
        categories: Final demand categories to cut. Defaults to the three consumption
            columns; GFCF is excluded by design.
        direct_emissions_extension: Opt-in for fuel tapes. Name the satellite account
            (EXIOBASE: ``"impacts"``) and the region's direct household emissions are cut
            by ``pct_reduction`` too — because the basket *is* the fuel being burnt.
            Leave it ``None``, the default, and those emissions instead follow the size of
            the household's whole basket, which is the right answer for a broad basket.

    Returns:
        A calculated IO system with the basket's demand reduced and nothing re-spent.

    Raises:
        ValueError: if ``pct_reduction`` exceeds 1.0 (cannot remove more than all demand).
    """
    if pct_reduction > 1.0:
        raise ValueError(f"pct_reduction must be at most 1.0, got {pct_reduction}")
    factor = 1.0 - pct_reduction
    cut = scale_final_demand(mrio, region, sector, factor=factor, categories=categories)
    if direct_emissions_extension is not None:
        cut = scale_direct_emissions(cut, region, factor, direct_emissions_extension, categories)
    return recalculate_from_final_demand(cut)
