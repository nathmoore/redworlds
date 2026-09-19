"""Load the tape records and the scenario concordance, and check them against a real table.

A tape record says everything physical about one of the game's tapes: which wing it is,
which region it acts on, which named basket of products it touches, and how far it can go.
The game sends only a tape id and an outcome fraction, so anything the engine needs and the
payload does not carry has to be here. The fields follow
docs/design/red_carbon_contract.md 4.2.

Two files, on purpose:

- ``data/tech_choices/options.toml`` — one record per tape, naming a ``scenario_category``.
- ``data/concordances/exiobase_to_scenario.csv`` — what products each category contains.

Keeping the baskets out of the tape records means two tapes can share a basket, and it
keeps the product labels in one file that can be checked in one pass.

That check is the point of this module. A product label is a long string with brackets,
semicolons and — in one case — a double space, and a label that does not match the table's
index is not an error anyone sees: pandas selects nothing and the tape silently scores
zero. ``validate_baskets`` turns that into an exception at load time, against the very
table the run will use, so a basket cannot be wrong for the table it is applied to.

References:
  - docs/design/red_carbon_contract.md 4.2 — the payload and the fields it implies
  - docs/backlog.md — T2
"""

import csv
import tomllib
from pathlib import Path
from typing import Any

import pymrio

_REPO_ROOT = Path(__file__).parents[3]
DEFAULT_OPTIONS_PATH = _REPO_ROOT / "data" / "tech_choices" / "options.toml"
DEFAULT_SCENARIO_PATH = _REPO_ROOT / "data" / "concordances" / "exiobase_to_scenario.csv"

# The three wings, as options.toml spells them at the top level.
WINGS: tuple[str, ...] = ("build", "swap", "reduce")

# Fields every record carries whatever its wing. The ceiling is here because the game's
# "tapes in stock" mechanic wants it; recording it with its basis is worth doing even while
# that mechanic is undecided, so a record without one is a record someone forgot to finish.
REQUIRED_FIELDS: tuple[str, ...] = (
    "key",
    "label",
    "status",
    "region_id",
    "scenario_category",
    "matrix_target",
    "regional_ceiling",
    "regional_ceiling_unit",
    "regional_ceiling_basis",
    "beta_day_assumption",
)


def load_scenario_concordance(path: Path | None = None) -> dict[str, list[str]]:
    """Return {scenario_category: [product label, ...]} from the concordance CSV.

    Args:
        path: CSV to read. Defaults to the EXIOBASE concordance in data/concordances/.

    Returns:
        Product labels in file order, so a basket reads the way it was written.
    """
    baskets: dict[str, list[str]] = {}
    with (path or DEFAULT_SCENARIO_PATH).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(line for line in handle if not line.lstrip().startswith("#")):
            baskets.setdefault(row["scenario_category"], []).append(row["exiobase_sector"])
    return baskets


def load_tape_records(path: Path | None = None) -> dict[str, dict[str, Any]]:
    """Return {tape key: record} from options.toml, with the wing folded into each record.

    Args:
        path: TOML to read. Defaults to data/tech_choices/options.toml.

    Returns:
        One entry per tape, keyed by the id the game sends. Each record gains a ``wing``
        field so a caller holding one record knows which wing it belongs to.

    Raises:
        ValueError: If a record is missing a required field, or two records share a key.
    """
    with (path or DEFAULT_OPTIONS_PATH).open("rb") as handle:
        contents = tomllib.load(handle)

    records: dict[str, dict[str, Any]] = {}
    for wing in WINGS:
        for record in contents.get(wing, []):
            missing = [field for field in REQUIRED_FIELDS if field not in record]
            if missing:
                raise ValueError(f"Tape record {record.get('key', '<no key>')!r} is missing {missing}")
            if record["key"] in records:
                raise ValueError(f"Two tape records share the key {record['key']!r}")
            records[record["key"]] = {**record, "wing": wing}
    return records


def validate_baskets(
    mrio: pymrio.IOSystem,
    baskets: dict[str, list[str]] | None = None,
    records: dict[str, dict[str, Any]] | None = None,
) -> None:
    """Check every basket against a real table, and every tape against the baskets.

    Raises rather than warns. A mistyped product label selects nothing in pandas and the
    tape scores zero with no error, which is the failure this whole module exists to stop.

    Args:
        mrio: The table the tapes will be applied to — the aggregated baseline in practice.
            Product labels are checked against its sector index.
        baskets: As ``load_scenario_concordance`` returns. Loaded from disk if omitted.
        records: As ``load_tape_records`` returns. Loaded from disk if omitted.

    Raises:
        ValueError: If a basket names a product the table does not have, if a basket is
            empty, or if a tape names a scenario category that does not exist.
    """
    baskets = load_scenario_concordance() if baskets is None else baskets
    records = load_tape_records() if records is None else records
    sectors = set(mrio.get_sectors())

    problems: list[str] = []
    for category, products in baskets.items():
        if not products:
            problems.append(f"basket {category!r} is empty")
        for product in products:
            if product not in sectors:
                problems.append(f"basket {category!r}: no product {product!r} in the table")

    for key, record in records.items():
        if record["scenario_category"] not in baskets:
            problems.append(f"tape {key!r} names unknown scenario_category {record['scenario_category']!r}")

    if problems:
        raise ValueError("Tape records do not match the table:\n  " + "\n  ".join(problems))


def basket_for(record: dict[str, Any], baskets: dict[str, list[str]]) -> list[str]:
    """Return the product labels a tape record acts on.

    Args:
        record: One record from ``load_tape_records``.
        baskets: As ``load_scenario_concordance`` returns.

    Returns:
        The product labels of the record's scenario category.
    """
    return baskets[record["scenario_category"]]
