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

A basket need not be cut evenly. ``weights`` gives each product its own multiplier on the
headline fraction, because products do not respond alike: a year added to a laptop removes a
quarter of its replacement demand, a year added to a washing machine removes a twelfth. The
shock stays exactly linear in ``pct_reduction``, so the game's outcome fraction still scales
one precomputed answer.

Fuel tapes get one extra step. Direct household emissions — the petrol and gas people
burn themselves, rather than buy embodied in something — belong to no product row, so by
default they follow the size of the household's whole shopping basket. Cut 5% of
everything and they fall 5%, which is right. But a tape that cuts vehicle fuel or bans
household gas is cutting the fuel itself, and those emissions should fall by the change
in the fuel, not by the change in total spend. Such a tape passes
``direct_emissions_extension`` and gets that behaviour; every other tape is untouched.
The characterised account does not separate those household emissions by fuel, so the tape
also supplies the attributed share. The action scales the whole selected ``F_Y`` column by
a factor that leaves the un-attributed share fixed; see ``scale_direct_emissions`` and the
fuel-apportionment backlog item.

With uneven weights those two ideas meet: "the basket's change" is no longer one number, so a
fuel tape must also name the product its direct emissions follow (``direct_emissions_driver``)
rather than letting them ride an average that describes nothing in particular.

This is a deliberate post-growth design choice (confirmed 2026-09-16): reduced consumption
is not redirected elsewhere and takes no rebound haircut. Emissions are credited on a
consumption basis, so a European cut in imported electronics is credited with the
abatement in the factories abroad. See docs/design/assumptions.md for the rationale.

References:
  - docs/design/red_carbon_contract.md §3 (rule RE2) and §5 (basket design)
  - docs/design/assumptions.md — post-growth rebalancing assumption
  - data/concordances/exiobase_to_scenario.csv — scenario keys → product baskets (to populate)
"""

from collections.abc import Mapping, Sequence

import pymrio

from redworlds.engine.io_tables import (
    CONSUMPTION_CATEGORIES,
    recalculate_from_final_demand,
    scale_direct_emissions,
    scale_final_demand_per_product,
)


def apply_reduce(
    mrio: pymrio.IOSystem,
    region: str,
    sector: str | Sequence[str],
    pct_reduction: float,
    categories: Sequence[str] = CONSUMPTION_CATEGORIES,
    direct_emissions_extension: str | None = None,
    weights: Mapping[str, float] | None = None,
    direct_emissions_driver: str | None = None,
    direct_emissions_share: float = 1.0,
) -> pymrio.IOSystem:
    """Apply a REDUCE action: cut a region's demand for a basket of products, no rebalancing.

    Args:
        mrio: The calculated baseline world. Not mutated; a calculated copy is returned.
        region: Consuming region label as it appears in ``mrio.Y`` (an EXIOBASE code, or a
            game region name after ``aggregate_regions``).
        sector: One product label or a basket of them. Translating a tape's scenario key
            into product labels is the job layer's task, not this function's.
        pct_reduction: Fraction of the basket's demand removed, at most 1.0 once ``weights``
            are applied. A negative value is a backfire (the game's outcome fraction can go
            below zero for REDUCE): demand rises instead.
        categories: Final demand categories to cut. Defaults to the three consumption
            columns; GFCF is excluded by design.
        direct_emissions_extension: Opt-in for fuel tapes. Name the satellite account
            (EXIOBASE: ``"impacts"``) and the region's direct household emissions are cut
            as well. Leave it ``None``, the default, and those emissions instead follow the
            size of the household's whole basket, which is right for a broad basket.
        weights: {product: multiplier on ``pct_reduction``}. Defaults to 1.0 for every
            product, which is a flat cut. A product's realised cut is
            ``pct_reduction × weights[product]``, so the shock stays exactly linear in
            ``pct_reduction`` and the game's outcome fraction still scales it.
        direct_emissions_driver: Which product's change the direct emissions follow. Only
            meaningful with ``direct_emissions_extension``. With flat weights every product
            moves together and this can be left ``None``; with uneven weights it cannot,
            because "the basket's change" is then several different numbers and the fuel
            burnt at home follows the fuel row, not the average.
        direct_emissions_share: Share of the selected direct-emissions column attributable
            to the driver. The rest is held unchanged; defaults to the former whole-column
            behaviour for callers that know the selected account is all in scope.

    Returns:
        A calculated IO system with the basket's demand reduced and nothing re-spent.

    Raises:
        ValueError: if a share is invalid, any realised cut exceeds 1.0 (cannot remove more
            than all demand), or ``direct_emissions_driver`` is not in the basket.
    """
    if not 0.0 <= direct_emissions_share <= 1.0:
        raise ValueError(f"direct_emissions_share must be in [0, 1]; got {direct_emissions_share}")
    sectors = [sector] if isinstance(sector, str) else list(sector)
    factors = {product: 1.0 - pct_reduction * (weights or {}).get(product, 1.0) for product in sectors}

    too_deep = {product: 1.0 - factor for product, factor in factors.items() if factor < 0.0}
    if too_deep:
        raise ValueError(f"realised reduction must be at most 1.0; got {too_deep}")

    cut = scale_final_demand_per_product(mrio, region, factors, categories=categories)

    if direct_emissions_extension is not None:
        if direct_emissions_driver is None:
            realised_cut = pct_reduction
        elif direct_emissions_driver in factors:
            realised_cut = 1.0 - factors[direct_emissions_driver]
        else:
            raise ValueError(f"direct_emissions_driver {direct_emissions_driver!r} is not in the basket {sectors}")
        direct_factor = 1.0 - realised_cut * direct_emissions_share
        cut = scale_direct_emissions(cut, region, direct_factor, direct_emissions_extension, categories)

    return recalculate_from_final_demand(cut)
