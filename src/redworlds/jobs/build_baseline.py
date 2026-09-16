"""One-off job: build and cache the 2050 baseline world.

The game's "now" is 2050 and every tape is scored against a do-nothing 2050–2100 baseline.
This job produces that baseline from the 2011 EXIOBASE table:

1. Load EXIOBASE 3.8.2 pxp for 2011.
2. Convert currency to 2026 constant million USD (engine/currency.py).
3. Endogenise capital using the 2011 capital use matrix (engine/capital.py).
4. Aggregate to the 7 game regions (engine/regions.py) — or keep full resolution and
   aggregate results; an open choice, see docs/backlog.md.
5. Step the world forward year by year to 2050 along SSP2 (jobs/apply_growth.py):
   population and GDP drive final demand; technology change enters as coefficient
   changes with columns rescaled to one; stressors scale with coefficients.
6. Continue to 2100 to produce the baseline emissions trajectory.
7. Calculate and cache: the 2050 IOSystem with its Leontief inverse, plus the trajectory.

Method: Wiebe et al. (2018), Cap et al. (2024). Results downstream are relative to this
baseline, so the recipe matters less than its consistency.

This is the only job on the MVP path. It runs when the recipe changes, not nightly.

References:
  - docs/design/assumptions.md — "The baseline is SSP2, built once from 2011 EXIOBASE data"
  - docs/design/architecture.md — data retained
"""

from pathlib import Path

import pymrio


def build_baseline(
    mrio_2011: pymrio.IOSystem,
    capital_use_path: Path | None,
    target_year: int = 2050,
) -> pymrio.IOSystem:
    """Build the baseline world for ``target_year`` from the 2011 EXIOBASE system.

    Args:
        mrio_2011: The raw 2011 EXIOBASE 3.8.2 pxp system, as parsed by pymrio.
        capital_use_path: Path to ``Kbar_exio_v3_8_2_2011_cfc_pxp.mat``; ``None`` skips
            capital endogenisation (for tests on the pymrio test world).
        target_year: The in-game year the baseline represents.

    Returns:
        A calculated IO system for ``target_year`` in 2026 constant million USD with
        capital endogenised. Persisting it is the caller's job.

    TODO: implement — see docs/backlog.md §Sequencing (GitHub issue pending)
    """
    raise NotImplementedError
