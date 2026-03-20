"""
Region aggregation: EXIOBASE ~49 regions → 7 Red Worlds game regions.

EXIOBASE 3.8.2 (pxp) uses ~49 country and rest-of-world region codes (ISO-2 for
countries; WA/WL/WE/WF/WM for rest-of-world blocks). Red Worlds aggregates these
into 7 game regions for legibility.

Game regions:
    1 — USA and Canada
    2 — Latin America and the Caribbean
    3 — Europe and Central Asia
    4 — Africa and Middle East
    5 — South Asia
    6 — Mainland East Asia
    7 — South East Asia and Pacific Ocean

The concordance lives in data/concordances/region_mapping.csv. Any EXIOBASE
region code not present in that file will raise a KeyError — this is intentional
so that missing mappings surface during development rather than silently
producing wrong results.

Aggregation approach follows the pymrio documentation:
    https://pymrio.readthedocs.io/en/latest/notebooks/aggregation_examples.html

country_converter (coco) is available for future extensions (e.g. dynamically
building concordances for new EXIOBASE versions) but the CSV is the primary source.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pymrio

_CONCORDANCE_PATH = Path(__file__).parents[3] / "data" / "concordances" / "region_mapping.csv"


def load_region_concordance() -> dict[str, str]:
    """
    Return {exiobase_region_code: game_region_name} from the concordance CSV.

    Lines beginning with '#' are treated as comments and skipped.
    """
    df = pd.read_csv(
        _CONCORDANCE_PATH,
        comment="#",
        names=["exiobase_region", "game_region_id", "game_region_name"],
        skiprows=1,  # skip the header row
    )
    return dict(zip(df["exiobase_region"], df["game_region_name"]))


def _build_region_agg(regions: list[str], concordance: dict[str, str]) -> dict[str, list[str]]:
    """
    Convert a flat {code: game_region} dict into the inverted format that
    pymrio.IOSystem.aggregate() expects: {game_region: [codes]}.

    Raises KeyError for any region code not in the concordance.
    """
    result: dict[str, list[str]] = {}
    for code in regions:
        game_region = concordance[code]  # intentional KeyError if missing
        result.setdefault(game_region, []).append(code)
    return result


def aggregate_regions(mrio: pymrio.IOSystem) -> pymrio.IOSystem:
    """
    Return a copy of mrio with regions aggregated from ~49 EXIOBASE codes
    to 7 game regions.

    The original mrio is not modified (pure function — uses mrio.copy()
    before calling aggregate(), which mutates in place).

    Raises:
        KeyError: if any region code in mrio is not present in the concordance CSV.
    """
    concordance = load_region_concordance()
    regions = list(mrio.get_regions())
    region_agg = _build_region_agg(regions, concordance)

    result = mrio.copy()
    result.aggregate(region_agg=region_agg)
    return result
