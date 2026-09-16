"""BUILD action: simulate construction of new low-carbon energy capacity.

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
        build_years: Number of years the construction runs (derived from the tape record).
        current_year: The current simulation year.

    Returns:
        Updated IO system with construction spending applied for ``current_year``.

    TODO: implement — see GitHub issue #6
    """
    raise NotImplementedError
