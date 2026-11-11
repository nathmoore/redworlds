"""Tests for the electricity step of the baseline walk (src/redworlds/engine/electricity.py).

pymrio's test world has one electricity sector, so these tests treat two of its sectors,
``electricity`` and ``mining``, as two generation technologies of ``reg1`` with made-up
prices. The function only needs a list of products and a price for each, which is what
lets it be tested without EXIOBASE.
"""

import numpy as np
import pymrio
import pytest

from redworlds.engine.electricity import (
    implied_prices,
    reliable_technologies,
    shift_electricity_mix,
    substitute_unreliable,
)
from redworlds.engine.io_tables import recalculate_from_technical_coefficients

REGION = "reg1"
PRICES = {"electricity": 2.0, "mining": 0.5}


def _physical_output(mrio: pymrio.IOSystem) -> dict[str, float]:
    """Each stand-in technology's output in physical units: money output over its price."""
    assert mrio.x is not None
    return {product: float(mrio.x.loc[(REGION, product), "indout"]) / price for product, price in PRICES.items()}


def _kwh_bought(mrio: pymrio.IOSystem) -> np.ndarray:
    """Physical units of the two technologies bought by each column of A."""
    assert mrio.A is not None
    rows = [(REGION, product) for product in PRICES]
    return mrio.A.loc[rows, :].div(list(PRICES.values()), axis="index").sum(axis="index").to_numpy()


def test_shift_gives_the_target_physical_shares(test_mrio: pymrio.IOSystem) -> None:
    """After re-solving, physical output of the technologies is in exactly the target shares."""
    shifted = shift_electricity_mix(test_mrio, REGION, {"electricity": 0.3, "mining": 0.7}, PRICES)
    solved = recalculate_from_technical_coefficients(shifted)

    output = _physical_output(solved)
    total = sum(output.values())
    assert output["electricity"] / total == pytest.approx(0.3)
    assert output["mining"] / total == pytest.approx(0.7)


def test_shift_conserves_each_buyers_kilowatt_hours(test_mrio: pymrio.IOSystem) -> None:
    """Every column buys the same physical amount as before; only its sources change."""
    shifted = shift_electricity_mix(test_mrio, REGION, {"electricity": 0.3, "mining": 0.7}, PRICES)

    np.testing.assert_allclose(_kwh_bought(shifted), _kwh_bought(test_mrio))


def test_shift_to_the_current_mix_changes_nothing(test_mrio: pymrio.IOSystem) -> None:
    """Asking for the shares a region already has leaves its physical output where it was."""
    before = _physical_output(test_mrio)
    total = sum(before.values())
    current = {product: amount / total for product, amount in before.items()}

    solved = recalculate_from_technical_coefficients(shift_electricity_mix(test_mrio, REGION, current, PRICES))

    after = _physical_output(solved)
    assert sum(after.values()) == pytest.approx(total)
    assert after["electricity"] == pytest.approx(before["electricity"])


def test_shift_leaves_other_rows_and_the_original_alone(test_mrio: pymrio.IOSystem) -> None:
    """Only the listed products' rows in the named region move, and the input is not mutated."""
    assert test_mrio.A is not None
    original = test_mrio.A.copy()

    shifted = shift_electricity_mix(test_mrio, REGION, {"electricity": 0.3, "mining": 0.7}, PRICES)

    assert shifted.A is not None
    np.testing.assert_allclose(test_mrio.A.to_numpy(), original.to_numpy())
    untouched = [row for row in original.index if row not in [(REGION, product) for product in PRICES]]
    np.testing.assert_allclose(shifted.A.loc[untouched, :].to_numpy(), original.loc[untouched, :].to_numpy())


def test_shift_rejects_bad_shares_and_missing_prices(test_mrio: pymrio.IOSystem) -> None:
    """Shares must be a proper split and every listed product needs a positive price."""
    with pytest.raises(ValueError, match="sum to one"):
        shift_electricity_mix(test_mrio, REGION, {"electricity": 0.3, "mining": 0.3}, PRICES)
    with pytest.raises(ValueError, match="sum to one"):
        shift_electricity_mix(test_mrio, REGION, {"electricity": 1.2, "mining": -0.2}, PRICES)
    with pytest.raises(ValueError, match="no positive price"):
        shift_electricity_mix(test_mrio, REGION, {"electricity": 0.3, "mining": 0.7}, {"electricity": 2.0})


def test_implied_prices_are_output_over_supply(test_mrio: pymrio.IOSystem) -> None:
    """A technology's price is its money output per physical unit; no supply means no price."""
    assert test_mrio.x is not None
    output = float(test_mrio.x.loc[(REGION, "electricity"), "indout"])

    prices = implied_prices(test_mrio, REGION, {"electricity": 50.0, "mining": 0.0})

    assert prices == {"electricity": pytest.approx(output / 50.0)}


def test_reliable_technologies_need_size_and_a_plausible_price() -> None:
    """Too little supply, or a price far from the regional mean, rules a technology out."""
    supply = {"coal": 600.0, "gas": 400.0, "solar": 50.0, "tide": 0.2}
    prices = {"coal": 100.0, "gas": 120.0, "solar": 10.0, "tide": 110.0}

    assert reliable_technologies(supply, prices) == {"coal", "gas"}


def test_substitute_unreliable_keeps_the_class_totals() -> None:
    """An unreliable technology's share goes to reliable ones of its class, pro rata."""
    targets = {"coal": 0.4, "gas": 0.2, "hydro": 0.1, "nuclear": 0.2, "solar": 0.1}
    classes = {"coal": "fossil", "gas": "fossil", "hydro": "clean", "nuclear": "clean", "solar": "clean"}

    shares, substituted = substitute_unreliable(targets, {"coal", "gas", "hydro", "nuclear"}, classes)

    assert substituted == pytest.approx(0.1)
    assert sum(shares.values()) == pytest.approx(1.0)
    assert shares["coal"] == pytest.approx(0.4)
    assert shares["hydro"] == pytest.approx(0.1 + 0.1 / 3)
    assert shares["nuclear"] == pytest.approx(0.2 + 0.2 / 3)


def test_substitute_unreliable_needs_a_host_in_the_class() -> None:
    """With no reliable technology of the class, there is nowhere honest to put the share."""
    targets = {"coal": 0.9, "solar": 0.1}
    classes = {"coal": "fossil", "solar": "clean"}

    with pytest.raises(ValueError, match="no reliable 'clean' technology"):
        substitute_unreliable(targets, {"coal"}, classes)
