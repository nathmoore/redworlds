"""Capital endogenisation: move capital goods consumption into the technical coefficients.

In a plain IO table, investment (gross fixed capital formation, GFCF) sits in its own
final-demand column and does not respond to changes in consumption: cut household demand
for computers and the computer factories' capital spending is untouched. Endogenising
capital (Södersten, Wood & Hertwich 2018) moves the depreciation-based flow of capital
goods into each industry from the GFCF column into the coefficient matrix A, so every
unit of output carries its share of construction, machinery and equipment. Only net
expansion remains as final demand.

Data: the capital use matrices published for EXIOBASE 3.8.2 (Wood & Södersten, Zenodo
record 7073276, CC-BY-4.0), product-by-product, one file per year, e.g.
``Kbar_exio_v3_8_2_2011_cfc_pxp.mat``. Kbar is the flow form in million EUR (consumption
of fixed capital); the coefficient form is K = Kbar · x̂⁻¹, the same normalisation as
A = Z · x̂⁻¹.

This runs once, at baseline construction (jobs/build_baseline.py). It is never applied per
tape. BUILD tapes still inject their construction capex explicitly: endogenised capital is
proportional to output, and a plant under construction produces nothing.

References:
  - docs/design/assumptions.md — "Capital is endogenised in the baseline"
  - docs/references.md — Södersten, Wood & Hertwich (2018)
  - docs/backlog.md — remaining checks (carrying K through the 2011 → 2050 extrapolation)
"""

from pathlib import Path

import pandas as pd
import pymrio

# EXIOBASE-specific: the Zenodo capital use matrices are indexed like EXIOBASE 3.8.2 pxp.
CAPITAL_USE_FILENAME_2011: str = "Kbar_exio_v3_8_2_2011_cfc_pxp.mat"


def load_capital_use(path: Path) -> pd.DataFrame:
    """Load a Kbar capital use matrix (.mat) as a DataFrame indexed like ``mrio.Z``.

    Args:
        path: Path to the ``.mat`` file for the baseline year.

    Returns:
        Flow-form capital use matrix in million EUR, rows and columns as (region, product).

    TODO: implement — see docs/backlog.md §Sequencing (GitHub issue pending)
    """
    raise NotImplementedError


def endogenise_capital(mrio: pymrio.IOSystem, capital_use: pd.DataFrame) -> pymrio.IOSystem:
    """Return a copy of ``mrio`` with capital goods consumption moved from GFCF into A.

    Steps:
    1. K = capital_use · x̂⁻¹ (coefficient form).
    2. A ← A + K.
    3. Subtract the endogenised flows from the GFCF column(s) of Y, leaving net expansion.
    4. Leave satellite accounts unchanged; recalculation is the caller's responsibility.

    Args:
        mrio: A calculated IO system (needs ``x``). Not mutated; a copy is returned.
        capital_use: Flow-form Kbar for the same year and classification as ``mrio``.

    Returns:
        IO system with capital endogenised, A and Y modified, ready for a full recalculation.

    TODO: implement — see docs/backlog.md §Sequencing (GitHub issue pending)
    """
    raise NotImplementedError
