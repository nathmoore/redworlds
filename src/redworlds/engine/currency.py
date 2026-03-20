"""
Currency conversion for EXIOBASE monetary values.

EXIOBASE 3.8.2 expresses all monetary values in 2011 million EUR at basic prices.
Basic prices are producer prices — what the seller receives — excluding taxes on
products and excluding trade and transport margins.

Red Worlds exposes all monetary values to players in 2026 constant million USD.

Conversion path:
    2011 MEUR  ×  EUR_USD_2011         →  2011 MUSD
    2011 MUSD  ×  CPI_2026_OVER_2011   →  2026 constant MUSD

Sources:
    EUR_USD_2011       — ECB annual average EUR/USD exchange rate, 2011
    CPI_2026_OVER_2011 — US BLS CPI-U (1982–84 = 100):
                         ~224.9 (2011 annual average) / ~335.0 (2026 projection)

This conversion is applied once during baseline construction (the pipeline that
transforms raw EXIOBASE 2011 into the stored BASELINE_2027 world). After that
step, all IO tables on disk and in memory are natively in 2026 constant million
USD — no per-action or per-player conversion is needed.

Satellite accounts (physical units, e.g. kg CO2) are not scaled here. Their
values are unchanged; only the monetary denominator (x) changes, so derived
intensity matrices (S, M) will be in physical-per-USD rather than
physical-per-MEUR. Total emissions (D = M × Y) are scale-invariant and correct.
"""

import copy

import pymrio

# --- Conversion constants ---

EUR_USD_2011: float = 1.3917
"""Average EUR/USD exchange rate, 2011 (ECB annual average)."""

CPI_2026_OVER_2011: float = 1.489
"""US BLS CPI-U ratio: 2026 annual average / 2011 annual average (approximate)."""

CONVERSION_FACTOR: float = EUR_USD_2011 * CPI_2026_OVER_2011
"""Combined factor to convert 2011 MEUR → 2026 constant MUSD. ≈ 2.072."""


# --- Conversion functions ---


def meur_2011_to_musd_2026(value: float) -> float:
    """Convert a scalar from 2011 million EUR to 2026 constant million USD."""
    return value * CONVERSION_FACTOR


def convert_mrio_currency(mrio: pymrio.IOSystem) -> pymrio.IOSystem:
    """
    Return a copy of mrio with monetary matrices rescaled from
    2011 million EUR to 2026 constant million USD.

    Scales Z, Y, and x (total output vector) if present. Does not touch
    satellite accounts — their units vary by extension and must be handled
    separately if monetary conversion is needed there.

    The original mrio is not modified (pure function).
    """
    result = copy.deepcopy(mrio)
    for attr in ("Z", "Y", "x"):
        matrix = getattr(result, attr, None)
        if matrix is not None:
            setattr(result, attr, matrix * CONVERSION_FACTOR)
    return result
