"""
Region aggregation: EXIOBASE 49 regions → 7 Red Worlds game regions.

EXIOBASE 3.8.2 (pxp) uses 49 country and rest-of-world region codes (ISO-2 for
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

The concordance lives in data/concordances/region_mapping.csv. Any region code not
present in the concordance raises a KeyError — this is intentional so that missing
mappings surface during development rather than silently producing wrong results.

Tests pass their own concordance (tests/fixtures/test_world_regions.csv) so the pymrio
test world can exercise the same code path.

Aggregation approach follows the pymrio documentation:
    https://pymrio.readthedocs.io/en/latest/notebooks/aggregation_examples.html
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pymrio

# EXIOBASE-specific: this concordance maps EXIOBASE 3.8.2 (pxp) region codes to 7 game regions.
# A different MRIO database (WIOD, Eora, Gloria) would need its own concordance CSV.
DEFAULT_CONCORDANCE_PATH = Path(__file__).parents[3] / "data" / "concordances" / "region_mapping.csv"


def load_region_concordance(path: Path | None = None) -> dict[str, str]:
    """
    Return {region_code: game_region_name} from a concordance CSV.

    The CSV has a header row and columns ``region, game_region_id, game_region_name``.
    Lines beginning with '#' are comments and skipped.

    Args:
        path: CSV to read. Defaults to the EXIOBASE concordance in data/concordances/.
    """
    df = pd.read_csv(
        path or DEFAULT_CONCORDANCE_PATH,
        comment="#",
        names=["region", "game_region_id", "game_region_name"],
        skiprows=1,  # skip the header row
    )
    return dict(zip(df["region"], df["game_region_name"], strict=True))


def _build_region_agg(regions: list[str], concordance: dict[str, str]) -> list[str]:
    """
    Return the aggregation vector pymrio.IOSystem.aggregate() expects: the new region name
    for each existing region, in the order of ``regions``.

    Raises KeyError for any region code not in the concordance.
    """
    return [concordance[code] for code in regions]  # intentional KeyError if missing


def aggregate_regions(mrio: pymrio.IOSystem, concordance: dict[str, str] | None = None) -> pymrio.IOSystem:
    """
    Return a copy of mrio with regions aggregated to game regions.

    The original mrio is not modified (pure function — uses mrio.copy()
    before calling aggregate(), which mutates in place).

    Args:
        mrio: The IO system to aggregate.
        concordance: {region_code: game_region_name}. Defaults to the EXIOBASE concordance.

    Raises:
        KeyError: if any region code in mrio is not present in the concordance.
    """
    if concordance is None:
        concordance = load_region_concordance()
    regions = list(mrio.get_regions())
    region_agg = _build_region_agg(regions, concordance)

    result = mrio.copy()
    result.aggregate(region_agg=region_agg)
    return result
