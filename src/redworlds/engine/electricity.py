"""The electricity step of the baseline walk: change a region's generation mix.

EXIOBASE splits electricity into one product per generation technology ("Electricity by
coal", "... by wind" and so on). A region's grid mix is therefore the mix of those products
that everybody buys from it. Moving the mix means changing which of them each buyer
purchases — in the coefficient matrix ``A`` for industries and in ``Y`` for final consumers.

**The step conserves kilowatt-hours, not money.** Each buyer keeps the amount of electricity
it bought; only the sources change. This matters because the table's money per kWh differs
several-fold between technologies in the same region (2011, Europe and Central Asia: about
122 million EUR per TWh for coal, 73 for nuclear, 16 for solar PV). Moving a euro of
purchases from coal to solar would silently multiply the kWh delivered. So purchases are
converted to physical units at each technology's own 2011 price, reallocated, and converted
back. A column's total spend changes as a result; the electricity it receives does not.

Using each technology's *own* price keeps that technology as the 2011 table describes it:
the same inputs and the same emissions per kWh. That is a limit as much as a feature — the
table's picture of a small technology can be badly wrong, and where it is, the technology
cannot be scaled up from it. ``reliable_technologies`` decides which ones can be trusted
and ``substitute_unreliable`` says what happens to the rest.

Nothing here re-solves the system. Apply the step to as many regions as needed, then call
``engine.io_tables.recalculate_from_technical_coefficients`` once.

References:
  - docs/plans/03-baseline-walk.md — the walk this is step 5 of
  - docs/design/assumptions.md — "The baseline walk: electricity"
  - actions/build.py — the BUILD operating phase, the single-technology ancestor of this
"""

from collections.abc import Mapping

import numpy as np
import pandas as pd
import pymrio

# EXIOBASE-specific: the extension and row holding physical energy supplied, in TJ.
ENERGY_EXTENSION: str = "satellite"
ENERGY_SUPPLY_STRESSOR: str = "Energy Carrier Supply: Total"
TJ_PER_TWH: float = 3_600.0

# A technology is trusted only if the 2011 table holds enough of it to describe it, and
# prices it within a plausible band of the region's average. All three are judgements, not
# measurements: they are set to exclude the cases where a technology's money and its
# physical output plainly do not describe the same thing (solar PV at one-eighth of the
# regional price per kWh; biomass at a hundred times it on a rounding-error of output).
MIN_SUPPLY_TWH: float = 1.0
MIN_SUPPLY_SHARE: float = 0.001
PRICE_BAND: float = 4.0

SHARE_TOLERANCE: float = 1e-9


def electricity_supply_twh(
    mrio: pymrio.IOSystem,
    region: str,
    products: list[str],
    energy_extension: str = ENERGY_EXTENSION,
    energy_stressor: str | tuple[str, ...] = ENERGY_SUPPLY_STRESSOR,
) -> dict[str, float]:
    """Return the physical electricity each product supplies in ``region``, in TWh."""
    account = getattr(mrio, energy_extension)
    supplied_tj = account.F.loc[energy_stressor]
    return {product: float(supplied_tj[(region, product)]) / TJ_PER_TWH for product in products}


def implied_prices(mrio: pymrio.IOSystem, region: str, supply_twh: Mapping[str, float]) -> dict[str, float]:
    """Return each technology's money output per TWh: the table's own basic price.

    Technologies with no physical supply have no price and are left out of the result.
    """
    if mrio.x is None:
        raise ValueError("implied_prices needs a calculated system")
    prices: dict[str, float] = {}
    for product, twh in supply_twh.items():
        if twh > 0.0:
            prices[product] = float(mrio.x.loc[(region, product), "indout"]) / twh
    return prices


def reliable_technologies(
    supply_twh: Mapping[str, float],
    prices: Mapping[str, float],
    min_supply_twh: float = MIN_SUPPLY_TWH,
    min_supply_share: float = MIN_SUPPLY_SHARE,
    price_band: float = PRICE_BAND,
) -> set[str]:
    """Return the technologies the table describes well enough to scale up.

    A technology qualifies when it supplies at least ``min_supply_twh`` and
    ``min_supply_share`` of the region's electricity, and its price lies within a factor of
    ``price_band`` of the region's generation-weighted mean price.
    """
    total_twh = sum(supply_twh.values())
    priced = {product: twh for product, twh in supply_twh.items() if product in prices and twh > 0.0}
    if total_twh <= 0.0 or not priced:
        return set()
    mean_price = sum(prices[product] * twh for product, twh in priced.items()) / sum(priced.values())

    reliable: set[str] = set()
    for product, twh in priced.items():
        large_enough = twh >= min_supply_twh and twh / total_twh >= min_supply_share
        plausibly_priced = mean_price / price_band <= prices[product] <= mean_price * price_band
        if large_enough and plausibly_priced:
            reliable.add(product)
    return reliable


def substitute_unreliable(
    target_shares: Mapping[str, float],
    reliable: set[str],
    technology_class: Mapping[str, str],
) -> tuple[dict[str, float], float]:
    """Move the share of unreliable technologies to reliable ones of the same class.

    A region whose 2011 table cannot represent solar PV still has to end up with the right
    amount of *clean* electricity, or the fossil share — which is what drives emissions —
    would be wrong. So an unreliable technology's share is handed to the region's reliable
    technologies of the same class (clean or fossil), in proportion to their own targets.
    Direct emissions come out right; the supply chain behind the substituted share is that
    of the stand-in technologies, which is the approximation.

    Args:
        target_shares: {product: share of the region's generation}. Sums to one.
        reliable: Products the table can represent, from :func:`reliable_technologies`.
        technology_class: {product: class label}, for example "clean" or "fossil".

    Returns:
        ``(shares, substituted)``: shares over the reliable products only, summing to one,
        and the fraction of generation that had to be represented by a stand-in.

    Raises:
        ValueError: If a class has an unreliable share to place and no reliable member.
    """
    shares = {product: share for product, share in target_shares.items() if product in reliable}
    substituted = 0.0
    for label in sorted(set(technology_class.values())):
        members = [product for product in target_shares if technology_class[product] == label]
        homeless = sum(target_shares[product] for product in members if product not in reliable)
        if homeless <= 0.0:
            continue
        hosts = [product for product in members if product in reliable]
        if not hosts:
            raise ValueError(f"no reliable {label!r} technology to stand in for a {homeless:.1%} share")
        host_total = sum(target_shares[product] for product in hosts)
        for product in hosts:
            weight = target_shares[product] / host_total if host_total > 0.0 else 1.0 / len(hosts)
            shares[product] += homeless * weight
        substituted += homeless
    return shares, substituted


def shift_electricity_mix(
    mrio: pymrio.IOSystem,
    region: str,
    target_shares: Mapping[str, float],
    prices: Mapping[str, float],
) -> pymrio.IOSystem:
    """Return a copy of ``mrio`` in which ``region`` generates electricity in new shares.

    Every buyer, anywhere, of the listed electricity products from ``region`` keeps the
    kilowatt-hours it bought and takes them in the target shares instead. Products not
    listed are left as they are. After the system is re-solved, the listed products'
    physical output is in exactly the target shares.

    The system is **not** recalculated: ``A`` and ``Y`` are changed and the caller re-solves
    once, after shifting every region it means to.

    Args:
        mrio: A calculated system. Not mutated.
        region: The generating region.
        target_shares: {product: share of the listed products' combined kWh}. Sums to one.
        prices: {product: money per kWh, in any consistent unit}, covering every listed
            product. Normally :func:`implied_prices` on the base-year table.

    Returns:
        An uncalculated copy with new ``A`` and ``Y``.

    Raises:
        ValueError: If shares are negative or do not sum to one, or a price is missing or
            not positive.
    """
    if mrio.A is None or mrio.Y is None:
        raise ValueError("shift_electricity_mix needs a system with A and Y")
    products = list(target_shares)
    share = np.array([target_shares[product] for product in products], dtype=float)
    if (share < 0.0).any() or abs(share.sum() - 1.0) > SHARE_TOLERANCE:
        raise ValueError(f"target shares must be non-negative and sum to one; got a total of {share.sum()}")
    missing = [product for product in products if prices.get(product, 0.0) <= 0.0]
    if missing:
        raise ValueError(f"no positive price for {missing}")
    price = np.array([prices[product] for product in products], dtype=float)

    rows = [(region, product) for product in products]
    result = mrio.copy()
    assert result.A is not None and result.Y is not None
    for frame in (result.A, result.Y):
        purchases = frame.loc[rows, :]
        kwh_per_column = purchases.div(price, axis="index").sum(axis="index")
        reallocated = np.outer(share * price, kwh_per_column.to_numpy())
        frame.loc[rows, :] = pd.DataFrame(reallocated, index=purchases.index, columns=purchases.columns)
    return result
