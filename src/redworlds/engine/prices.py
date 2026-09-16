"""
Price type conversion for player-facing monetary values.

EXIOBASE stores monetary values in basic prices: what the producer receives,
excluding taxes on products and trade/transport margins. Player-facing costs —
BUILD budgets, SWAP costs, scenario totals — should be in purchaser prices:
the full amount the buyer actually pays.

    Purchaser price = Basic price + Taxes on products + Trade margins + Transport margins

EXIOBASE carries the data for a full conversion via its TT (taxes and subsidies on
products) and TTM (trade and transport margins) matrices. The correct long-term
implementation reads those matrices and applies them sector-by-sector.

For now, a universal markup factor approximates the gap. This is the standard
simplification used in scenario tools when exact sector breakdown is not the point.
Typical markup range: 1.15–1.25 for construction/manufactured goods; lower for
services; higher for tax-heavy energy products.

Proper TT/TTM-based conversion is a docs/backlog.md item.

Note: a separate real→nominal (inflation) conversion is needed once the overnight
growth job advances simulation years past the 2026 base year. That is out of scope
here — all IO tables stay in constant 2026 million USD until then.
"""

# EXIOBASE-specific: this markup approximates EXIOBASE's TT + TTM matrices for 3.8.2 pxp.
BASIC_TO_PURCHASER_MARKUP: float = 1.20
"""Universal markup from basic prices to purchaser prices.

Approximates taxes on products + trade margins + transport margins.
Typical range for construction/goods: 1.15–1.25. See docs/design/assumptions.md.
"""


def basic_to_purchaser(value: float) -> float:
    """Convert a monetary value from basic prices to purchaser prices."""
    return value * BASIC_TO_PURCHASER_MARKUP


def purchaser_to_basic(value: float) -> float:
    """Convert a monetary value from purchaser prices to basic prices."""
    return value / BASIC_TO_PURCHASER_MARKUP
