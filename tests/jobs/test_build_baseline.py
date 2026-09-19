"""Tests for the baseline job (src/redworlds/jobs/build_baseline.py).

Unit tests run on the pymrio test world with the fixture concordance, so they exercise the
real composition — aggregate, solve, endogenise, solve again — without EXIOBASE. Reading the
Kbar file is ``main``'s job, so these pass a synthetic one straight in; the real loader is
covered by the integration tests in tests/engine/test_capital.py.

The integration test builds the real cached world and asserts the thing T1 exists to
guarantee: the world total still reads 44.5 Gt CO2e after aggregation and endogenisation,
matching examples/03_first_reduce_number.ipynb. Endogenising capital moves money between Z
and Y and leaves F and F_Y alone, so the footprint must not move at all.
"""

from pathlib import Path
from typing import Any

import pandas as pd
import pymrio
import pytest

from redworlds.config import load_config
from redworlds.engine.capital import (
    GFCF_COLUMN,
    aggregate_capital_use,
    load_capital_use,
    negative_net_investment,
)
from redworlds.engine.regions import load_region_concordance
from redworlds.engine.scoring import total_emissions
from redworlds.jobs.build_baseline import BASELINE_NAME, EXIOBASE_2011_PXP, TABLE_FORMAT, build_baseline

CONCORDANCE_PATH = Path(__file__).parents[1] / "fixtures" / "test_world_regions.csv"

# The world total in examples/03_first_reduce_number.ipynb, in kg CO2e. Capital
# endogenisation must not move it: it changes A and Y, never F or F_Y.
NOTEBOOK_03_WORLD_TOTAL_GT = 44.5

# Share of each intermediate flow the synthetic test-world Kbar treats as depreciation.
SYNTHETIC_DEPRECIATION_SHARE = 0.05


def _table(mrio: pymrio.IOSystem, name: str) -> Any:
    """Fetch a pymrio table; they are Optional / dynamic, which upsets the type checker."""
    table = getattr(mrio, name)
    assert table is not None, f"{name} is not set — has the system been calculated?"
    return table


@pytest.fixture
def concordance() -> dict[str, str]:
    """The test world's region concordance: 6 pymrio regions → 5 game regions."""
    return load_region_concordance(CONCORDANCE_PATH)


@pytest.fixture
def synthetic_capital_use(test_mrio: pymrio.IOSystem) -> pd.DataFrame:
    """A plausible Kbar for the test world: a fixed share of every intermediate flow.

    The numbers do not matter — what these tests check is the accounting and the wiring.
    Taking a share of Z keeps the capital mix and the magnitudes sane at any classification.
    """
    return _table(test_mrio, "Z") * SYNTHETIC_DEPRECIATION_SHARE


def test_aggregates_to_game_regions(test_mrio, concordance) -> None:
    """The returned world carries game region names, not the source database's codes."""
    world = build_baseline(test_mrio, capital_use=None, concordance=concordance)

    assert set(world.get_regions()) == set(concordance.values())
    assert len(list(world.get_regions())) < len(list(test_mrio.get_regions()))


def test_returns_a_calculated_system(test_mrio, concordance) -> None:
    """Aggregation drops A and L; the job has to rebuild them or nothing downstream works."""
    world = build_baseline(test_mrio, capital_use=None, concordance=concordance)

    assert world is not test_mrio
    assert world.A is not None
    assert world.L is not None
    assert world.x is not None


def test_aggregation_conserves_the_world_footprint(test_mrio, concordance) -> None:
    """Grouping regions moves nothing in or out of the world total."""
    world = build_baseline(test_mrio, capital_use=None, concordance=concordance)

    assert total_emissions(world, extension="emissions", stressor=("emission_type1", "air")) == pytest.approx(
        total_emissions(test_mrio, extension="emissions", stressor=("emission_type1", "air"))
    )


def test_endogenising_capital_conserves_the_world_footprint(test_mrio, concordance, synthetic_capital_use) -> None:
    """The T1 guarantee in miniature: capital moves money, not emissions."""
    plain = build_baseline(test_mrio, capital_use=None, concordance=concordance)
    endogenised = build_baseline(test_mrio, capital_use=synthetic_capital_use, concordance=concordance)

    stressor = ("emission_type1", "air")
    assert total_emissions(endogenised, extension="emissions", stressor=stressor) == pytest.approx(
        total_emissions(plain, extension="emissions", stressor=stressor)
    )


def test_endogenising_capital_moves_gfcf_into_a(test_mrio, concordance, synthetic_capital_use) -> None:
    """Capital leaves the investment column and arrives in the coefficient matrix."""
    plain = build_baseline(test_mrio, capital_use=None, concordance=concordance)
    endogenised = build_baseline(test_mrio, capital_use=synthetic_capital_use, concordance=concordance)

    assert endogenised.A is not None and plain.A is not None
    assert (endogenised.A.to_numpy() >= plain.A.to_numpy() - 1e-12).all()
    assert endogenised.A.to_numpy().sum() > plain.A.to_numpy().sum()

    gfcf_before = _table(plain, "Y").loc[:, (slice(None), GFCF_COLUMN)].to_numpy().sum()
    gfcf_after = _table(endogenised, "Y").loc[:, (slice(None), GFCF_COLUMN)].to_numpy().sum()
    assert gfcf_after < gfcf_before


def test_build_baseline_does_not_mutate_its_input(test_mrio, concordance) -> None:
    """The job is a composition of pure functions and must behave like one."""
    original_regions = list(test_mrio.get_regions())
    original_y = _table(test_mrio, "Y").copy()

    build_baseline(test_mrio, capital_use=None, concordance=concordance)

    assert list(test_mrio.get_regions()) == original_regions
    pd.testing.assert_frame_equal(_table(test_mrio, "Y"), original_y)


def test_aggregate_capital_use_conserves_the_total(test_mrio, concordance) -> None:
    """Grouping a Kbar's regions must not create or destroy capital flows."""
    world = build_baseline(test_mrio, capital_use=None, concordance=concordance)
    capital_use = pd.DataFrame(1.0, index=_table(test_mrio, "Z").index, columns=_table(test_mrio, "Z").columns)

    aggregated = aggregate_capital_use(capital_use, concordance, _table(world, "A").index)

    assert aggregated.to_numpy().sum() == pytest.approx(capital_use.to_numpy().sum())
    pd.testing.assert_index_equal(aggregated.index, _table(world, "A").index)
    pd.testing.assert_index_equal(aggregated.columns, _table(world, "A").index)


def test_aggregate_capital_use_raises_on_a_missing_label(test_mrio, concordance) -> None:
    """A Kbar that cannot cover the table's index is a mislabelled file, not a warning."""
    world = build_baseline(test_mrio, capital_use=None, concordance=concordance)
    capital_use = pd.DataFrame(1.0, index=_table(test_mrio, "Z").index, columns=_table(test_mrio, "Z").columns)
    short = capital_use.drop(index=capital_use.index[0], columns=capital_use.columns[0])

    with pytest.raises(ValueError, match="does not cover"):
        aggregate_capital_use(short, concordance, _table(world, "A").index)


def test_negative_net_investment_splits_by_supplying_region(test_mrio, concordance) -> None:
    """The diagnostic has to separate trade mismatch from genuine disinvestment."""
    world = build_baseline(test_mrio, capital_use=None, concordance=concordance)
    regions = list(world.get_regions())
    home, away = regions[0], regions[1]
    sector = list(world.get_sectors())[0]
    _table(world, "Y").loc[(home, sector), (home, GFCF_COLUMN)] = -1.0
    _table(world, "Y").loc[(away, sector), (home, GFCF_COLUMN)] = -2.0

    negative = negative_net_investment(world)

    assert len(negative) == 2
    assert negative["value"].sum() == pytest.approx(-3.0)
    assert negative.set_index("supplying_region").loc[home, "same_region"]
    assert not negative.set_index("supplying_region").loc[away, "same_region"]


def test_negative_net_investment_is_empty_when_nothing_is_negative(test_mrio, concordance) -> None:
    """The test world invests more than it depreciates, so the frame comes back empty."""
    world = build_baseline(test_mrio, capital_use=None, concordance=concordance)

    assert negative_net_investment(world).empty


@pytest.mark.integration
def test_real_baseline_matches_notebook_03(tmp_path) -> None:
    """T1's done condition: the cached world reads 44.5 Gt and reloads in seconds.

    Slow — this is the whole job. It parses EXIOBASE, aggregates, endogenises the real Kbar
    and solves twice, then round-trips the result through disk to prove the cache is usable.
    """
    config = load_config()
    exiobase_path = Path(config["data"]["exiobase_path"]) / EXIOBASE_2011_PXP
    capital_use_path = Path(config["data"]["capital_use_path"])
    if not exiobase_path.exists() or not capital_use_path.exists():
        pytest.skip("integration test needs the EXIOBASE and Kbar downloads — see data/README.md")

    world = build_baseline(pymrio.parse_exiobase3(exiobase_path), load_capital_use(capital_use_path))

    assert len(list(world.get_regions())) == 7
    assert total_emissions(world) / 1e12 == pytest.approx(NOTEBOOK_03_WORLD_TOTAL_GT, abs=0.1)

    destination = tmp_path / BASELINE_NAME
    world.save_all(destination, table_format=TABLE_FORMAT)
    reloaded = pymrio.load_all(destination)

    assert _table(reloaded, "L") is not None
    assert total_emissions(reloaded) == pytest.approx(total_emissions(world))
