"""BUILD action: construction capex and the post-build electricity-mix change.

The game's finale resolves a tape into an outcome fraction; the job handler derives
from the tape record:
  - A build budget (basic prices, 2026 constant MUSD)
  - A build period (years), including any modifier time delta

Red Worlds then:
1. Injects the CapEx into gross fixed capital formation, split across construction,
   machinery, electrical equipment and business services, over the build period.
2. After the build period, changes the electricity sector's technology mix (A and S).
3. Optionally rebalances (the reallocation flag) so the injection crowds out other
   investment instead of adding to it.

References:
  - docs/design/game_mechanics.md — BUILD input/output contract
  - docs/design/assumptions.md — where the money goes; capital endogenised in the baseline
  - data/tech_choices/options.toml — compatible technologies and scenario tags
"""

from collections.abc import Mapping, Sequence

import pymrio

from redworlds.engine.balancing import rebalance_economy
from redworlds.engine.currency import CONVERSION_FACTOR
from redworlds.engine.io_tables import GFCF, recalculate_from_final_demand, recalculate_from_technical_coefficients
from redworlds.engine.prices import purchaser_to_basic

# Wood/Wiebe et al. (2018), SI Table SI1: nuclear's capital expenditure split.
DEFAULT_CAPEX_SPLIT: dict[str, float] = {
    "Construction work (45)": 0.40,
    "Machinery and equipment n.e.c. (29)": 0.42,
    "Electrical machinery and apparatus n.e.c. (31)": 0.09,
    "Other business services (74)": 0.09,
}

FOSSIL_ELECTRICITY: tuple[str, ...] = (
    "Electricity by coal",
    "Electricity by gas",
    "Electricity by petroleum and other oil derivatives",
)
ENERGY_SUPPLY_STRESSOR: str = "Energy Carrier Supply: Total"
ENERGY_EXTENSION: str = "satellite"
TJ_PER_TWH: float = 3_600.0


def apply_build(
    mrio: pymrio.IOSystem,
    region: str,
    technology: str,
    budget: float,
    build_years: int,
    current_year: int,
    capex_split: Mapping[str, float] = DEFAULT_CAPEX_SPLIT,
    reallocate: bool = False,
) -> pymrio.IOSystem:
    """Apply one annual construction-phase injection.

    This compatibility entry point models the Y-side phase only. The operating phase needs
    a physical generation quantity as well as a technology and is handled separately by
    :func:`apply_build_operation`.

    Args:
        mrio: The player's current IO system (will not be mutated; a copy is returned).
        region: Amalgamated game region (e.g. "Europe and Central Asia").
        technology: Technology key from data/tech_choices/options.toml (e.g. "offshore_wind").
        budget: Total build budget in the IO system's currency unit.
        build_years: Number of years the construction runs (derived from the tape record).
        current_year: One-indexed year of construction. Values after ``build_years`` return
            an unchanged copy.
        capex_split: Product shares of total capex; defaults to Wood/Wiebe's nuclear split.
        reallocate: If true, crowd the injection out of other GFCF instead of adding it.

    Returns:
        Calculated IO system with one year's construction spending applied.

    Raises:
        ValueError: If the time, budget, or split is invalid.
    """
    del technology  # the record supplies a technology-specific split when it differs
    if build_years <= 0:
        raise ValueError(f"build_years must be positive; got {build_years}")
    if current_year <= 0:
        raise ValueError(f"current_year must be one-indexed and positive; got {current_year}")
    if budget < 0.0:
        raise ValueError(f"budget must be non-negative; got {budget}")
    if current_year > build_years or budget == 0.0:
        return recalculate_from_final_demand(mrio)
    return apply_build_construction(mrio, region, budget / build_years, capex_split, reallocate)


def apply_build_construction(
    mrio: pymrio.IOSystem,
    region: str,
    annual_budget_purchaser: float,
    capex_split: Mapping[str, float] = DEFAULT_CAPEX_SPLIT,
    reallocate: bool = False,
) -> pymrio.IOSystem:
    """Inject one build year's capex into the region's GFCF column.

    Player-facing budgets are 2026 MUSD at purchaser prices; cached-table money is at basic
    prices. The universal 1.20 conversion is the documented temporary approximation until
    EXIOBASE's sector-specific tax and margin matrices are wired.
    """
    if annual_budget_purchaser < 0.0:
        raise ValueError(f"annual_budget_purchaser must be non-negative; got {annual_budget_purchaser}")
    if not capex_split or abs(sum(capex_split.values()) - 1.0) > 1e-9 or any(v < 0.0 for v in capex_split.values()):
        raise ValueError("capex_split must contain non-negative shares summing to 1.0")

    result = mrio.copy()
    assert result.Y is not None
    annual_budget_basic = purchaser_to_basic(annual_budget_purchaser) / CONVERSION_FACTOR
    for sector, share in capex_split.items():
        result.Y.loc[(region, sector), (region, GFCF)] += annual_budget_basic * share

    if reallocate and annual_budget_basic:
        result = rebalance_economy(
            result,
            region,
            -annual_budget_basic,
            categories=(GFCF,),
            excluded_sectors=tuple(capex_split),
        )
    return recalculate_from_final_demand(result)


def generation_twh_to_basic_output(
    mrio: pymrio.IOSystem,
    region: str,
    technology_sector: str,
    generation_twh: float,
    energy_extension: str = ENERGY_EXTENSION,
    energy_stressor: str | tuple[str, ...] = ENERGY_SUPPLY_STRESSOR,
) -> float:
    """Price a physical electricity quantity using the table's own technology row.

    EXIOBASE's energy-carrier-supply row reports TJ supplied by each generation product.
    Dividing the sector's monetary output by that physical output gives its basic price,
    preserving the table's own technology-specific valuation.
    """
    if generation_twh < 0.0:
        raise ValueError(f"generation_twh must be non-negative; got {generation_twh}")
    if mrio.x is None:
        raise ValueError("generation_twh_to_basic_output needs a calculated system")
    account = getattr(mrio, energy_extension)
    supplied_tj = float(account.F.loc[energy_stressor, (region, technology_sector)])
    if supplied_tj <= 0.0:
        raise ValueError(f"{region}/{technology_sector} has no positive {energy_stressor!r} value")
    output = float(mrio.x.loc[(region, technology_sector), "indout"])
    return generation_twh * TJ_PER_TWH * output / supplied_tj


def apply_build_operation(
    mrio: pymrio.IOSystem,
    region: str,
    technology_sector: str,
    generation_twh: float,
    deployment_fraction: float = 1.0,
    fossil_sectors: Sequence[str] = FOSSIL_ELECTRICITY,
    energy_extension: str = ENERGY_EXTENSION,
    energy_stressor: str | tuple[str, ...] = ENERGY_SUPPLY_STRESSOR,
) -> pymrio.IOSystem:
    """Replace fossil electricity inputs with a built technology and re-solve ``A``.

    The built TWh is valued at the technology sector's own basic price. That monetary output
    is moved proportionally out of fossil-electricity purchases by the region's industries
    and final consumers. Every affected A or Y column keeps the same total, so the operation
    changes the technology recipe rather than the size of the economy.

    ``deployment_fraction`` is explicit because the Leontief solve is non-linear in an
    A-matrix change. Export samples 0.25, 0.5, 0.75 and 1.0 rather than pretending the full
    result scales linearly.
    """
    if not 0.0 <= deployment_fraction <= 1.0:
        raise ValueError(f"deployment_fraction must be in [0, 1]; got {deployment_fraction}")
    if mrio.A is None or mrio.Y is None or mrio.x is None:
        raise ValueError("apply_build_operation needs a calculated system")

    replacement_output = (
        generation_twh_to_basic_output(
            mrio,
            region,
            technology_sector,
            generation_twh,
            energy_extension,
            energy_stressor,
        )
        * deployment_fraction
    )
    if replacement_output == 0.0:
        return recalculate_from_technical_coefficients(mrio)

    industry_columns = (region, slice(None))
    final_columns = (region, slice(None))
    fossil_rows = (slice(None), list(fossil_sectors))

    fossil_coefficients = mrio.A.loc[fossil_rows, industry_columns]
    using_output = mrio.x.loc[industry_columns, "indout"]
    intermediate_fossil = fossil_coefficients.mul(using_output, axis="columns")
    final_fossil = mrio.Y.loc[fossil_rows, final_columns]
    fossil_total = float(intermediate_fossil.to_numpy().sum() + final_fossil.to_numpy().sum())
    if replacement_output > fossil_total:
        raise ValueError(
            f"built output {replacement_output:g} exceeds the region's fossil-electricity purchases {fossil_total:g}"
        )
    fraction = replacement_output / fossil_total

    result = mrio.copy()
    assert result.A is not None and result.Y is not None
    removed_a = result.A.loc[fossil_rows, industry_columns] * fraction
    result.A.loc[fossil_rows, industry_columns] -= removed_a
    result.A.loc[(region, technology_sector), industry_columns] += removed_a.sum(axis=0)

    removed_y = result.Y.loc[fossil_rows, final_columns] * fraction
    result.Y.loc[fossil_rows, final_columns] -= removed_y
    result.Y.loc[(region, technology_sector), final_columns] += removed_y.sum(axis=0)
    return recalculate_from_technical_coefficients(result)
