"""Step an IO world forward by one year under the CMIP7 Medium scenario.

Used inside jobs/build_baseline.py to walk the 2011 table to 2050 and on to 2100
(population and GDP drive final demand; technology change enters as coefficient
changes with columns rescaled to one; stressors scale with coefficients — Wiebe et al.
2018). In phase 2 the same function advances per-player worlds nightly.

References:
  - docs/design/assumptions.md — the baseline is CMIP7 Medium, built once
  - docs/design/architecture.md — two phases
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
