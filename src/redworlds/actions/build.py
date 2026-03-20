"""BUILD action: simulate construction of new low-carbon energy capacity.

The player selects a technology (e.g. offshore wind, nuclear), a region, and a
number of units. The Decarbonator Deck produces:
  - A build budget (currency units)
  - A build period (years), including any overrun

Red Worlds then:
1. Spreads the CapEx across the IO table's construction sectors over the build period.
2. After the build period, adjusts the energy mix of the target scenario sector to
   reflect the new capacity.
3. Rebalances money flows across the economy to maintain a closed system.

References:
  - docs/design/game_mechanics.md — BUILD input/output contract
  - docs/design/assumptions.md — CapEx spreading and parallel construction assumptions
  - data/tech_choices/options.toml — compatible technologies and scenario tags
"""

import pymrio


def apply_build(
    mrio: pymrio.IOSystem,
    region: str,
    technology: str,
    budget: float,
    build_years: int,
    current_year: int,
) -> pymrio.IOSystem:
    """Apply a BUILD action to a player's IO system.

    CapEx is spread linearly over ``build_years`` starting from ``current_year``.
    Energy mix changes are applied once the full build period is complete.

    Args:
        mrio: The player's current IO system (will not be mutated; a copy is returned).
        region: Amalgamated game region (e.g. "Europe and Central Asia").
        technology: Technology key from data/tech_choices/options.toml (e.g. "offshore_wind").
        budget: Total build budget in the IO system's currency unit.
        build_years: Number of years the construction runs (from the Decarbonator Deck output).
        current_year: The current simulation year.

    Returns:
        Updated IO system with construction spending applied for ``current_year``.

    TODO: implement — see GitHub issue #6
    """
    raise NotImplementedError
