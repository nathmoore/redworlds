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

The ``.mat`` file holds a 9800 x 9800 sparse matrix plus its own labels. Its 200 product
labels are character-for-character identical to EXIOBASE's ``products.txt``; its region
labels are ISO-3 codes (``AUT``, ``ROM``, ``WWM``) where EXIOBASE uses ISO-2 (``AT``,
``RO``, ``WM``), so they are translated on load by :data:`_ISO3_TO_EXIOBASE_REGION`.
Both axes are region-major (all 200 products of region 1, then region 2, ...), matching
EXIOBASE's own ordering. Rows are the capital good supplied (region, product); columns
are the industry consuming it (region, product).

This runs once, at baseline construction (jobs/build_baseline.py). It is never applied per
tape. BUILD tapes still inject their construction capex explicitly: endogenised capital is
proportional to output, and a plant under construction produces nothing.

References:
  - docs/design/assumptions.md — "Capital is endogenised in the baseline"
  - docs/references.md — Södersten, Wood & Hertwich (2018)
  - docs/backlog.md — remaining checks (carrying K through the 2011 → 2050 extrapolation)
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pymrio
import scipy.io

# EXIOBASE-specific: the Zenodo capital use matrices are indexed like EXIOBASE 3.8.2 pxp.
CAPITAL_USE_FILENAME_2011: str = "Kbar_exio_v3_8_2_2011_cfc_pxp.mat"

# EXIOBASE-specific: the final demand column that holds gross investment.
GFCF_COLUMN: str = "Gross fixed capital formation"

# EXIOBASE-specific: the Kbar files label regions with ISO-3 codes, EXIOBASE with ISO-2.
# The five rest-of-world blocks are WWA/WWL/WWE/WWF/WWM there and WA/WL/WE/WF/WM here.
# An unknown code raises a KeyError on load — better a loud failure than a silent mislabel.
_ISO3_TO_EXIOBASE_REGION: dict[str, str] = {
    "AUT": "AT", "BEL": "BE", "BGR": "BG", "CYP": "CY", "CZE": "CZ", "DEU": "DE", "DNK": "DK",
    "EST": "EE", "ESP": "ES", "FIN": "FI", "FRA": "FR", "GRC": "GR", "HRV": "HR", "HUN": "HU",
    "IRL": "IE", "ITA": "IT", "LTU": "LT", "LUX": "LU", "LVA": "LV", "MLT": "MT", "NLD": "NL",
    "POL": "PL", "PRT": "PT", "ROM": "RO", "SWE": "SE", "SVN": "SI", "SVK": "SK", "GBR": "GB",
    "USA": "US", "JPN": "JP", "CHN": "CN", "CAN": "CA", "KOR": "KR", "BRA": "BR", "IND": "IN",
    "MEX": "MX", "RUS": "RU", "AUS": "AU", "CHE": "CH", "TUR": "TR", "TWN": "TW", "NOR": "NO",
    "IDN": "ID", "ZAF": "ZA", "WWA": "WA", "WWL": "WL", "WWE": "WE", "WWF": "WF", "WWM": "WM",
}  # fmt: skip


def _labels_from_mat(cell_array: np.ndarray) -> list[str]:
    """Unwrap a MATLAB cell array of strings, saved by scipy as a nested object array."""
    return [str(cell[0]) for cell in cell_array.ravel()]


def load_capital_use(path: Path) -> pd.DataFrame:
    """Load a Kbar capital use matrix (.mat) as a DataFrame indexed like ``mrio.Z``.

    Args:
        path: Path to the ``.mat`` file for the baseline year.

    Returns:
        Flow-form capital use matrix in million EUR, rows and columns as (region, product).
    """
    contents = scipy.io.loadmat(path)
    regions = [_ISO3_TO_EXIOBASE_REGION[code] for code in _labels_from_mat(contents["countries"])]
    products = _labels_from_mat(contents["prodLabels"])
    axis = pd.MultiIndex.from_product([regions, products], names=["region", "sector"])

    flows = contents["Kbar"].toarray()  # sparse on disk, dense here: A and Y arithmetic needs it dense
    return pd.DataFrame(flows, index=axis, columns=axis)


def endogenise_capital(mrio: pymrio.IOSystem, capital_use: pd.DataFrame) -> pymrio.IOSystem:
    """Return a copy of ``mrio`` with capital goods consumption moved from GFCF into A.

    Steps:
    1. K = capital_use · x̂⁻¹ (coefficient form). Sectors with zero output get a zero
       coefficient rather than an infinity.
    2. A ← A + K.
    3. Subtract the endogenised flows from the GFCF column of each using region's final
       demand, leaving net expansion.
    4. Leave the satellite flows (F, F_Y) unchanged; everything derived from A and Y is
       cleared so the caller's ``calc_all()`` rebuilds L, x, Z and the extension accounts.

    Net investment can go negative for individual (capital good, region) cells, where
    consumption of fixed capital in 2011 exceeded that region's gross investment in that
    product. This is left as it falls: clipping it would break the accounting identity
    between what leaves Y and what enters intermediate demand.

    Args:
        mrio: A calculated IO system (needs ``x``). Not mutated; a copy is returned.
        capital_use: Flow-form Kbar for the same year and classification as ``mrio``.

    Returns:
        IO system with capital endogenised, A and Y modified, ready for a full recalculation.

    Raises:
        ValueError: If ``mrio`` has not been calculated yet (no x), so K cannot be normalised.
    """
    if mrio.x is None or mrio.Y is None:
        raise ValueError("endogenise_capital needs a calculated system — call mrio.calc_all() first.")

    output = mrio.x["indout"]
    # x[j] == 0 means the sector produces nothing, so it consumes no capital per unit either.
    reciprocal_output = pd.Series(0.0, index=output.index)
    produces = output != 0
    reciprocal_output[produces] = 1.0 / output[produces]
    capital_coefficients = capital_use.mul(reciprocal_output, axis="columns")

    # Capital used by every industry in a region is withdrawn from that region's GFCF column.
    use_by_region = capital_use.T.groupby(level="region").sum().T
    final_demand = mrio.Y.copy()
    for region in use_by_region.columns:
        final_demand[(region, GFCF_COLUMN)] -= use_by_region[region]

    result = mrio.copy()
    result.reset_all_full()  # keeps Z, Y, F, F_Y; drops A, L, x, S, M and the D_* accounts
    result.A = mrio.A + capital_coefficients
    result.Y = final_demand
    result.Z = None  # forces calc_all() down the "A and Y given" path: L, then x, then Z
    return result
