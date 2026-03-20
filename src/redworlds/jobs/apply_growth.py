"""Overnight job: advance a player's IO world by one simulation year.

Applies projected economic growth and population changes to the IO tables,
producing the 'climate emissions of the year with no action taken' baseline.

This job runs once per day, before the new scenario is presented to the player.

References:
  - docs/design/assumptions.md — growth projection assumptions
  - docs/design/architecture.md — overnight job flow
"""

import pymrio


def apply_growth(
    mrio: pymrio.IOSystem,
    year: int,
) -> pymrio.IOSystem:
    """Advance a player's IO system by one simulation year.

    Scales demand, production, and population vectors to reflect projected growth
    for ``year``. Returns an updated IO system representing the new year's baseline
    (i.e. emissions with no player action taken).

    Args:
        mrio: The player's IO system for the previous simulation year.
        year: The new simulation year being advanced to.

    Returns:
        Updated IO system scaled to ``year`` with recalculated baseline emissions.

    TODO: implement — see GitHub issue #9
    """
    raise NotImplementedError
