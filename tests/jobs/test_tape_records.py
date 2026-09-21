"""Tests for the tape record loader (src/redworlds/jobs/tape_records.py).

Unit tests write their own tiny options.toml and concordance to a tmp_path and check them
against the pymrio test world, so they exercise the validation rather than the committed
data. The committed data is checked by the integration test at the bottom, against the
cached baseline — which is the only check that means anything, because a product label is
only right or wrong relative to a particular table.
"""

from pathlib import Path
from typing import Any

import pymrio
import pytest

from redworlds.config import load_config
from redworlds.jobs.build_baseline import BASELINE_NAME
from redworlds.jobs.tape_records import (
    DEFAULT_OPTIONS_PATH,
    DEFAULT_SCENARIO_PATH,
    basket_for,
    load_scenario_concordance,
    load_scenario_weights,
    load_tape_records,
    validate_baskets,
    weights_for,
)

# The three tapes sprint 2 solves. The other six carry their fields but are not run.
BETA_DAY_REDUCE_TAPES = ("eca_buy_less", "eca_extended_product_lifetimes", "eca_remote_work_commuters")


def _write_records(path: Path, key: str = "test_tape", **overrides: Any) -> Path:
    """Write a minimal but complete one-record options.toml."""
    fields = {
        "key": key,
        "label": "Test Tape",
        "status": "ready",
        "region_id": 3,
        "scenario_category": "test_basket",
        "matrix_target": ["Y"],
        "regional_ceiling": 0.5,
        "regional_ceiling_unit": "fraction",
        "regional_ceiling_basis": "a test",
        "beta_day_assumption": "a test",
        **overrides,
    }
    lines = ["[[reduce]]"]
    for name, value in fields.items():
        if value is None:
            continue
        rendered = f'"{value}"' if isinstance(value, str) else str(value).replace("'", '"').lower()
        lines.append(f"{name} = {rendered}" if not isinstance(value, str) else f"{name} = {rendered}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _write_basket(path: Path, products: list[str], category: str = "test_basket") -> Path:
    """Write a minimal concordance CSV, comments included so the comment skipping is used."""
    rows = ["scenario_category,exiobase_sector,weight,notes", "# a comment line the reader must skip"]
    rows += [f'{category},"{product}",1.0,test' for product in products]
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return path


def test_loads_baskets_in_file_order(tmp_path, test_mrio) -> None:
    """A basket reads the way it was written; order is not sorted away."""
    sectors = list(test_mrio.get_sectors())
    path = _write_basket(tmp_path / "c.csv", [sectors[2], sectors[0], sectors[1]])

    assert load_scenario_concordance(path)["test_basket"] == [sectors[2], sectors[0], sectors[1]]


def test_records_carry_their_wing(tmp_path) -> None:
    """A caller holding one record must know which wing it belongs to."""
    records = load_tape_records(_write_records(tmp_path / "o.toml"))

    assert records["test_tape"]["wing"] == "reduce"


def test_missing_required_field_raises(tmp_path) -> None:
    """A record without a ceiling is a record someone forgot to finish."""
    with pytest.raises(ValueError, match="regional_ceiling_basis"):
        load_tape_records(_write_records(tmp_path / "o.toml", regional_ceiling_basis=None))


def test_duplicate_key_raises(tmp_path) -> None:
    """Two tapes sharing an id would silently shadow one another."""
    path = tmp_path / "o.toml"
    body = _write_records(path).read_text()
    path.write_text(body + "\n" + body)

    with pytest.raises(ValueError, match="share the key"):
        load_tape_records(path)


def test_mistyped_product_label_raises(tmp_path, test_mrio) -> None:
    """The failure this module exists to stop: a label that selects nothing."""
    sectors = list(test_mrio.get_sectors())
    baskets = load_scenario_concordance(_write_basket(tmp_path / "c.csv", [sectors[0], "Not A Real Product"]))
    records = load_tape_records(_write_records(tmp_path / "o.toml"))

    with pytest.raises(ValueError, match="Not A Real Product"):
        validate_baskets(test_mrio, baskets, records)


def test_empty_basket_raises(tmp_path, test_mrio) -> None:
    """An empty basket cuts nothing and would score zero without complaining."""
    baskets = {"test_basket": []}
    records = load_tape_records(_write_records(tmp_path / "o.toml"))

    with pytest.raises(ValueError, match="is empty"):
        validate_baskets(test_mrio, baskets, records)


def test_unknown_scenario_category_raises(tmp_path, test_mrio) -> None:
    """A tape pointing at a basket that does not exist fails at load, not at solve."""
    sectors = list(test_mrio.get_sectors())
    baskets = load_scenario_concordance(_write_basket(tmp_path / "c.csv", [sectors[0]], category="other"))
    records = load_tape_records(_write_records(tmp_path / "o.toml"))

    with pytest.raises(ValueError, match="unknown scenario_category"):
        validate_baskets(test_mrio, baskets, records)


def test_valid_records_pass_quietly(tmp_path, test_mrio) -> None:
    """The happy path returns None and raises nothing."""
    sectors = list(test_mrio.get_sectors())
    baskets = load_scenario_concordance(_write_basket(tmp_path / "c.csv", [sectors[0], sectors[1]]))
    records = load_tape_records(_write_records(tmp_path / "o.toml"))

    assert validate_baskets(test_mrio, baskets, records) is None
    assert basket_for(records["test_tape"], baskets) == [sectors[0], sectors[1]]


def test_committed_files_hold_all_nine_tapes() -> None:
    """The committed records cover the game's nine tapes, three of them ready to solve."""
    records = load_tape_records(DEFAULT_OPTIONS_PATH)
    baskets = load_scenario_concordance(DEFAULT_SCENARIO_PATH)

    assert len(records) == 9
    ready = {key for key, record in records.items() if record["status"] == "ready"}
    assert ready == set(BETA_DAY_REDUCE_TAPES)
    assert all(record["wing"] == "reduce" for key, record in records.items() if key in ready)
    # Every ready tape's basket must be non-empty, or sprint 2 exports a zero.
    assert all(basket_for(records[key], baskets) for key in ready)


def test_committed_ceilings_all_state_their_basis() -> None:
    """A ceiling without a basis is a number nobody can check or defend."""
    for key, record in load_tape_records(DEFAULT_OPTIONS_PATH).items():
        assert record["regional_ceiling_basis"].strip(), f"{key} has an empty ceiling basis"
        assert record["regional_ceiling_unit"].strip(), f"{key} has an empty ceiling unit"


def test_remote_work_names_the_product_driving_direct_emissions() -> None:
    """A mixed basket must say which product the fuel burnt at home follows.

    The basket holds the forecourt margin and public transport as well as the two fuels, so
    "the basket's change" is several numbers. Direct household emissions follow the petrol
    row specifically, and a record that opted into the correction without naming a driver
    would quietly average them.
    """
    records = load_tape_records(DEFAULT_OPTIONS_PATH)
    weights = load_scenario_weights(DEFAULT_SCENARIO_PATH)
    record = records["eca_remote_work_commuters"]

    assert record["direct_emissions_extension"] == "impacts"
    assert record["direct_emissions_driver"] == "Motor Gasoline"
    assert record["direct_emissions_driver"] in weights_for(record, weights)


def test_only_the_lifetimes_basket_is_weighted() -> None:
    """Weights are a real modelling claim, so a basket carrying them should mean to.

    Extending a product's life removes N / (life + N) of its replacement demand, which
    differs per product — that is this tape's whole mechanism. Every other basket is flat,
    and a stray weight elsewhere would be a typo nobody would otherwise catch.
    """
    weights = load_scenario_weights(DEFAULT_SCENARIO_PATH)
    uneven = {category for category, products in weights.items() if set(products.values()) != {1.0}}

    assert uneven == {"appliances_and_devices", "commuting_vehicle_fuel"}
    assert len(weights["appliances_and_devices"]) == 8
    # Short-lived products lose more of their replacement flow than long-lived ones.
    devices = weights["appliances_and_devices"]["Office machinery and computers (30)"]
    white_goods = weights["appliances_and_devices"]["Electrical machinery and apparatus n.e.c. (31)"]
    assert devices > white_goods


@pytest.mark.integration
def test_committed_baskets_match_the_cached_baseline() -> None:
    """The check that means anything: every label exists in the table the tapes will run on."""
    worlds_path = Path(load_config()["data"]["worlds_path"]) / BASELINE_NAME
    if not worlds_path.exists():
        pytest.skip(f"no cached baseline at {worlds_path} — run `just baseline`")

    validate_baskets(pymrio.load_all(worlds_path))
