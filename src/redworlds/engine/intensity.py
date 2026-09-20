"""How much carbon a euro of demand carries, and how that falls between 2011 and 2050.

Every tape is solved on the 2011 EXIOBASE table, but every tape is *played* in 2050. A euro
of demand removed in 2011 carries more carbon than the same euro removed in 2050 will,
because the grid gets cleaner, coal leaves the mix and industry gets more efficient. Without
a correction, every number the game shows is a 2011 number wearing a 2050 label.

**The correction is in two stages, and they are kept apart on purpose.**

    2011 ──── observation ────▶ 2027 ──── scenario ────▶ 2050

The two halves are different kinds of claim and deserve different amounts of trust:

- **2011 → 2027 is a matter of record.** We know what happened. Solar and wind costs
  collapsed, European coal generation fell sharply, and the carbon intensity of world output
  fell by about 2% a year throughout. This half is checkable against published series, and it
  can be improved without anyone agreeing about the future.
- **2027 → 2050 is a scenario.** Nobody knows. SSP2 is the defensible choice and is what the
  game's baseline assumes, but it is a choice.

Collapsing them into one number buries the half we can verify inside the half we cannot, and
hides which part of a disagreement is actually in dispute. Splitting them costs nothing —
they compose by multiplication — and it lets the observed half be replaced with real data
long before the scenario half needs the full SSP2 walk.

**Both are still stand-ins.** The right answer is to walk the table forward year by year,
with population and GDP driving final demand and technology change entering as coefficient
changes — `jobs/apply_growth.py`, which does not exist yet. These scalars stand in until it
does.

**Why shipping a stand-in is safe here.** It scales every tape by the same factor, so it
cannot make one tape look better than another, and it cannot tilt a wing. A wrong value costs
accuracy on the headline figure, not fairness between choices — a different order of risk
from, say, a wrong product basket. That is the test for whether a simplification is
shippable.

**Why this is a module and not a constant in a job.** Everything that needs the correction
asks here, so replacing a stand-in with real data is one edit in one file with one test, and
nothing downstream has to know it happened. That is the pattern for every deliberate
simplification in this repo: give it a named seam, say what the real method is and why it was
deferred, and leave a backlog item. A simplification with a name is a decision; the same
number inlined in three jobs is debt.

References:
  - docs/design/units_and_currency.md §4 — why this is not a currency conversion
  - docs/design/tape_records.md §8 — what every solved number is still missing
  - docs/backlog.md — the walk that replaces both stages
  - docs/references.md — the sources behind the observed stage

TODO: replace with the real walk — see docs/backlog.md §Sequencing item 5b (GitHub issue pending)
"""

# The baseline table's year: EXIOBASE 3.8.2 pxp, and the year the Kbar capital matrix covers.
BASE_YEAR: int = 2011

# The present day, where observation stops and scenario begins. Deliberately a year ahead of
# the money base year (2026, engine/currency.py): what a euro is worth and what a euro emits
# are independent axes, and pinning them to the same year would only be cosmetic.
PIVOT_YEAR: int = 2027

# The game's "now", and the year every tape is scored from.
TARGET_YEAR: int = 2050

# Stage one, 2011 → 2027. OBSERVED.
#
# The carbon intensity of world economic output fell about 2.1% a year through this period:
# global CO2 intensity of GDP was 27% below its 2010 level by 2025 (Enerdata), which is
# -2.08%/yr compounded, consistent with the -2.2%/yr Enerdata reports for 2010-2019 directly.
# Compounded over the sixteen years from 2011 to 2027 that gives 0.71.
#
# Why a *world* figure and not a European one, when the tapes act on Region 3: the accounting
# here is consumption-based, so a European household's footprint is mostly the intensity of
# the supply chains it buys from, which are global. Region 3's own grid decarbonised faster
# than the world's (EU electricity intensity fell 26% in the decade to 2024, reaching
# 213 gCO2/kWh — EEA), but using that rate would overstate how fast the imported half of the
# footprint cleaned up.
OBSERVED_2011_TO_2027: float = 0.71
"""Sourced and checkable. See docs/references.md."""

# Stage two, 2027 → 2050. SCENARIO.
#
# Continues the observed 2.08%/yr decline across the twenty-three years to 2050, which is
# roughly what a middle-of-the-road SSP2 world does: no collapse, no breakthrough, the
# existing trend running on. This is the half nobody can check, and the half a real SSP2 run
# should replace first.
SCENARIO_2027_TO_2050: float = 0.62
"""Trend continuation standing in for SSP2. The weakest number in the export."""


def intensity_scalar(year: int = TARGET_YEAR) -> float:
    """Return the factor converting a 2011-basis emissions figure to ``year``.

    Multiply a tape's annual delta by this to state it in the target year's intensities. The
    factor is positive, so abatement stays negative.

    Args:
        year: The year to correct to. ``BASE_YEAR`` (no correction), ``PIVOT_YEAR`` (the
            observed half alone) or ``TARGET_YEAR`` (both stages). Years in between need the
            real walk.

    Returns:
        A positive multiplier. 1.0 means as carbon-intense per euro as 2011.

    Raises:
        ValueError: If asked for a year these two stages cannot answer for. Interpolating
            would invent a number; returning the 2050 factor for 2035 would be wrong by a
            decade with nothing to show for it.
    """
    if year == BASE_YEAR:
        return 1.0
    if year == PIVOT_YEAR:
        return OBSERVED_2011_TO_2027
    if year == TARGET_YEAR:
        return OBSERVED_2011_TO_2027 * SCENARIO_2027_TO_2050
    raise ValueError(
        f"intensity_scalar answers for {BASE_YEAR}, {PIVOT_YEAR} and {TARGET_YEAR} while the "
        f"correction is two scalars; asked for {year}. Per-year answers need the SSP2 walk — "
        f"see docs/backlog.md."
    )
