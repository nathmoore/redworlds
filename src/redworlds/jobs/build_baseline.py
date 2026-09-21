"""One-off job: build and cache the baseline world.

The game's "now" is 2050 and every tape is scored against a do-nothing 2050–2100 baseline.
Getting there from the 2011 EXIOBASE table is two pieces of work, and this job currently
does the first:

1. **Done here.** Load EXIOBASE 3.8.2 pxp for 2011, aggregate to the 7 game regions,
   endogenise capital using the 2011 capital use matrix, solve, and persist.
2. **Not here yet.** Step the world forward to 2050 along SSP2 — population and GDP drive
   final demand, technology change enters as coefficient changes with columns rescaled to
   one, stressors scale with coefficients — then on to 2100 for the baseline trajectory.

Splitting it this way is deliberate. The SSP2 walk is the judgement-heavy step and it wants
real tape numbers to sanity-check against, which means the tapes have to run first. They can:
nothing about a tape's mechanism depends on the walk, only its magnitude, and a 2011-basis
number labelled as such is worth more now than a 2050 number in a fortnight. Every export is
a re-run of this job by design, so the second table costs the game no code.

The cached world is left in EXIOBASE's own units — 2011 million EUR at basic prices. The
conversion to 2026 constant USD (engine/currency.py) is a single scalar on Z, Y and x; it
does not touch emissions, and applying it at export time keeps the cached artefact one step
from source. See docs/backlog.md §Sequencing.

Aggregating before endogenising rather than after is what makes this job minutes instead of
an afternoon: the Leontief inverse is then 1,400 x 1,400 rather than 9,800 x 9,800, and the
answer is the same because both A and K are flows over output and flows aggregate linearly.

Method: Södersten, Wood & Hertwich (2018) for capital; Wiebe et al. (2018), Cap et al. (2024)
for the walk to come. Results downstream are relative to this baseline, so the recipe matters
less than its consistency.

This is the only job on the MVP path. It runs when the recipe changes, not nightly.

References:
  - docs/design/assumptions.md — "The baseline is SSP2, built once from 2011 EXIOBASE data"
  - docs/design/architecture.md — data retained
  - docs/backlog.md — T1, and the negative net-investment decision of 2026-09-18

TODO: the SSP2 2011 → 2050 walk — see GitHub issue #17
"""

from pathlib import Path

import pandas as pd
import pymrio

from redworlds.config import load_config
from redworlds.engine.capital import (
    aggregate_capital_use,
    endogenise_capital,
    load_capital_use,
    negative_net_investment,
)
from redworlds.engine.regions import aggregate_regions, load_region_concordance
from redworlds.engine.scoring import total_emissions

# EXIOBASE-specific: the folder pymrio's parser expects for the 2011 product-by-product table.
EXIOBASE_2011_PXP: str = "IOT_2011_pxp"

# Name of the cached world this job writes. The year and the region count are in the name
# because the SSP2 walk will produce a sibling (baseline_2050_agg7) rather than replace it.
BASELINE_NAME: str = "baseline_2011_agg7"

# Parquet rather than pymrio's default tab-separated text: the point of caching is that a
# second process loads the Leontief inverse in seconds, and 1,400 x 1,400 floats as text is
# a slow read of a large file.
TABLE_FORMAT: str = "parquet"


def build_baseline(
    mrio_2011: pymrio.IOSystem,
    capital_use: pd.DataFrame | None,
    concordance: dict[str, str] | None = None,
) -> pymrio.IOSystem:
    """Build the aggregated, capital-endogenised baseline world from the 2011 table.

    Reading the Kbar file is :func:`main`'s job, not this one's, so the composition can be
    tested on the pymrio test world without a ``.mat`` round trip.

    Args:
        mrio_2011: The raw 2011 EXIOBASE 3.8.2 pxp system, as parsed by pymrio. It need not
            be calculated; this job solves it after aggregating.
        capital_use: Flow-form Kbar at the source database's region resolution, as
            ``engine.capital.load_capital_use`` returns it. ``None`` skips capital
            endogenisation and returns the aggregated world.
        concordance: {region_code: game_region_name}. Defaults to the EXIOBASE concordance
            in data/concordances/.

    Returns:
        A calculated IO system at 7 game regions, in 2011 million EUR, with capital
        endogenised. Persisting it is the caller's job — see :func:`main`.
    """
    if concordance is None:
        concordance = load_region_concordance()

    world = aggregate_regions(mrio_2011, concordance)
    world.calc_all()  # aggregate() drops A and L (coefficients cannot be summed); rebuild them
    if capital_use is None:
        return world

    assert world.A is not None
    aggregated = aggregate_capital_use(capital_use, concordance, world.A.index)
    world = endogenise_capital(world, aggregated)
    world.calc_all()
    return world


def _report_negative_net_investment(world: pymrio.IOSystem) -> None:
    """Print the negative-GFCF diagnostic the 2026-09-18 decision asked this job to record.

    The decision was to keep negative net investment as it falls, on the condition that the
    split between trade mismatch and genuine same-region disinvestment gets looked at. If the
    total is dominated by same-region cells, that decision is worth revisiting.
    """
    negative = negative_net_investment(world)
    if negative.empty:
        print("Negative net investment: none.")
        return

    total = negative["value"].sum()
    same = negative[negative["same_region"]]
    cross = negative[~negative["same_region"]]
    print(
        f"Negative net investment: {len(negative):,} cells, {total / 1e6:,.2f} trillion EUR.\n"
        f"  same-region (genuine disinvestment): {len(same):,} cells, {same['value'].sum() / 1e6:,.2f} T EUR\n"
        f"  cross-region (trade mismatch):       {len(cross):,} cells, {cross['value'].sum() / 1e6:,.2f} T EUR"
    )


def main() -> None:
    """Build the baseline from the configured EXIOBASE download and cache it.

    Run with ``just baseline``. Overwrites the cached world in place.
    """
    config = load_config()
    exiobase_path = Path(config["data"]["exiobase_path"]) / EXIOBASE_2011_PXP
    capital_use_path = Path(config["data"]["capital_use_path"])
    destination = Path(config["data"]["worlds_path"]) / BASELINE_NAME

    print(f"Parsing {exiobase_path} ...")
    mrio_2011 = pymrio.parse_exiobase3(exiobase_path)

    print("Aggregating to game regions and endogenising capital ...")
    world = build_baseline(mrio_2011, load_capital_use(capital_use_path))

    _report_negative_net_investment(world)
    print(f"World total: {total_emissions(world) / 1e12:.1f} Gt CO2e/yr")

    destination.mkdir(parents=True, exist_ok=True)
    world.save_all(destination, table_format=TABLE_FORMAT)
    print(f"Saved to {destination}")


if __name__ == "__main__":
    main()
