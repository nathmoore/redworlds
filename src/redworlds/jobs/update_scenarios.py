"""Overnight job: generate a new daily scenario for players.

A scenario represents a specific emissions category (e.g. 'European residential
heating') for a given simulation year and region. The game designer specifies a
target category and region; this module maps that to EXIOBASE sectors using the
concordance tables in data/concordances/.

The scenario output is what the player sees on the Red Carbon website and what
the Decarbonator Deck acts on.

References:
  - docs/design/architecture.md — scenario generation flow
  - data/concordances/exiobase_to_scenario.csv — category-to-sector mapping
  - data/concordances/region_mapping.csv — game region to EXIOBASE region mapping
"""

import pymrio


def generate_scenario(
    mrio: pymrio.IOSystem,
    category: str,
    game_region: str,
    year: int,
) -> dict:
    """Generate a daily scenario from an emissions category and region.

    Looks up the EXIOBASE sectors corresponding to ``category`` and ``game_region``
    via the concordance tables, then extracts the relevant slice of the IO system
    to produce the scenario data sent to the Red Carbon front end.

    Args:
        mrio: The player's IO system for the current simulation year.
        category: Scenario emissions category (e.g. "residential_heating").
            Must match a key in data/concordances/exiobase_to_scenario.csv.
        game_region: Amalgamated game region (e.g. "Europe and Central Asia").
            Must match a key in data/concordances/region_mapping.csv.
        year: The current simulation year.

    Returns:
        A dict containing the scenario data for the front end, including the
        baseline emissions value, region, category, and year.

    TODO: implement — see GitHub issue #11
    """
    raise NotImplementedError
