"""Smart-grid efficiency shock on technical electricity coefficients."""

from collections.abc import Sequence

import pymrio

from redworlds.engine.io_tables import recalculate_from_technical_coefficients

ELECTRICITY_GENERATION: tuple[str, ...] = (
    "Electricity by coal",
    "Electricity by gas",
    "Electricity by nuclear",
    "Electricity by hydro",
    "Electricity by wind",
    "Electricity by petroleum and other oil derivatives",
    "Electricity by biomass and waste",
    "Electricity by solar photovoltaic",
    "Electricity by solar thermal",
    "Electricity by tide, wave, ocean",
    "Electricity by Geothermal",
)
ELECTRICITY_DELIVERY: tuple[str, ...] = (
    "Transmission services of electricity",
    "Distribution and trade services of electricity",
)


def apply_grid_efficiency(
    mrio: pymrio.IOSystem,
    region: str,
    deployment_fraction: float = 1.0,
    baseline_loss_fraction: float = 0.062,
    target_loss_fraction: float = 0.040,
    demand_response_fraction: float = 0.020,
    generation_sectors: Sequence[str] = ELECTRICITY_GENERATION,
    delivery_sectors: Sequence[str] = ELECTRICITY_DELIVERY,
) -> pymrio.IOSystem:
    """Reduce grid losses and non-grid industries' electricity inputs.

    Loss efficiency acts only on generation inputs to the transmission and distribution
    columns. Demand response acts on generation *and delivery* inputs to every other
    industry in the changed region. No generation technology gains share, and Y is unchanged.
    """
    if not 0.0 <= deployment_fraction <= 1.0:
        raise ValueError(f"deployment_fraction must be in [0, 1]; got {deployment_fraction}")
    if not 0.0 <= target_loss_fraction < baseline_loss_fraction < 1.0:
        raise ValueError("loss fractions must satisfy 0 <= target < baseline < 1")
    if not 0.0 <= demand_response_fraction <= 1.0:
        raise ValueError(f"demand_response_fraction must be in [0, 1]; got {demand_response_fraction}")
    if mrio.A is None:
        raise ValueError("apply_grid_efficiency needs a calculated system")

    result = mrio.copy()
    assert result.A is not None
    generation_rows = (slice(None), list(generation_sectors))
    delivery_columns = (region, list(delivery_sectors))
    full_loss_factor = (1.0 - baseline_loss_fraction) / (1.0 - target_loss_fraction)
    loss_factor = 1.0 - deployment_fraction * (1.0 - full_loss_factor)
    result.A.loc[generation_rows, delivery_columns] *= loss_factor

    other_sectors = [sector for sector in mrio.get_sectors() if sector not in delivery_sectors]
    other_columns = (region, other_sectors)
    electricity_rows = (slice(None), list(generation_sectors) + list(delivery_sectors))
    response_factor = 1.0 - deployment_fraction * demand_response_fraction
    result.A.loc[electricity_rows, other_columns] *= response_factor
    return recalculate_from_technical_coefficients(result)
