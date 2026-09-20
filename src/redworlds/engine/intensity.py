"""How much carbon a euro of demand carries, and how that falls between 2011 and 2050.

Every tape is solved on the 2011 EXIOBASE table, but every tape is *played* in 2050. A euro
of demand removed in 2011 carries more carbon than the same euro removed in 2050 will,
because the grid gets cleaner, coal leaves the mix and industry gets more efficient. Without
a correction, every number the game shows is a 2011 number wearing a 2050 label.

**This module is a deliberate stand-in.** The correct answer is to walk the table forward —
population and GDP driving final demand, technology change entering as coefficient changes,
stressors scaling with coefficients — which is `jobs/apply_growth.py` and the SSP2 baseline
that does not exist yet. Until it does, one documented scalar multiplies every tape's annual
delta.

**Why the simplification is safe to ship.** It moves every tape by the same factor, so it
cannot tilt one wing against another, and game balance is the thing a wrong number here
would damage. It changes the absolute figure on the board, which is an accuracy question,
not a fairness one. That is a very different risk from, say, getting one basket wrong.

**Why it is one function and not a constant sprinkled through the jobs.** Everything that
needs the correction asks here, so replacing the stand-in with a real walk is one edit in one
file with one test, and nothing downstream has to know it happened. That is the pattern this
repo uses for every deliberate simplification: give it a named seam, say in the docstring
what the real method is and why it was deferred, and leave a backlog item. A simplification
with a name is a decision; the same number inlined in three jobs is technical debt.

References:
  - docs/design/tape_records.md §6 — what every solved number is still missing
  - docs/design/assumptions.md — the intensity correction as a stated assumption
  - docs/backlog.md — the 2011 → 2026 → 2050 walk that replaces this
  - docs/design/red_carbon_contract.md §4.4 — `intensity_scalar_2050` in the export

TODO: replace with the real walk — see docs/backlog.md §Sequencing item 5b (GitHub issue pending)
"""

# The baseline table's year. EXIOBASE 3.8.2 pxp, the year the Kbar capital matrix also covers.
BASE_YEAR: int = 2011

# The game's "now", and the year every tape is scored from.
TARGET_YEAR: int = 2050

# Emissions intensity of demand in 2050 relative to 2011, as one factor on every tape.
#
# 0.6 is a working figure, NOT yet sourced — it stands for "roughly a 40% fall in tonnes per
# euro over forty years", which is the order an SSP2-style CO2-intensity-of-GDP decline
# gives. It is the single least defensible number in the whole export and it scales every
# headline the game shows, so it should not survive contact with a real source.
#
# Two things worth knowing before replacing it. First, the honest replacement is not a better
# scalar but the walk itself, in two stages: 2011 to 2026 corrected against what actually
# happened to the energy system (the 2011 table predates the collapse in solar and wind cost
# and most of Europe's coal retirement, so it is dirtier than the world already is), then
# 2026 to 2050 along SSP2. Second, the two stages want different evidence — the first is
# observation and the second is scenario — so they should not be collapsed into one factor
# even when both exist.
INTENSITY_SCALAR_2050: float = 0.6
"""Provisional. See the module docstring; the real correction is the SSP2 walk."""


def intensity_scalar(year: int = TARGET_YEAR) -> float:
    """Return the factor converting a 2011-basis emissions delta to ``year``.

    Multiply a tape's annual delta by this to state it in the target year's intensities.
    The sign is unaffected: the factor is positive and abatement stays negative.

    Args:
        year: The year to correct to. Only ``TARGET_YEAR`` is supported while the correction
            is a single scalar; the argument exists so callers are already written against
            the interface the real walk will need.

    Returns:
        A positive multiplier. 1.0 would mean 2050 is as carbon-intense per euro as 2011.

    Raises:
        ValueError: If asked for a year the stand-in cannot answer for. Failing loudly beats
            silently returning the 2050 factor for 2035 and being wrong by a decade.
    """
    if year != TARGET_YEAR:
        raise ValueError(
            f"intensity_scalar only answers for {TARGET_YEAR} while the correction is one scalar; "
            f"asked for {year}. The per-year answer needs the SSP2 walk — see docs/backlog.md."
        )
    return INTENSITY_SCALAR_2050
