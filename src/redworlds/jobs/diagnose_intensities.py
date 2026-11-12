"""Find the products whose emission intensity in a region cannot be trusted.

EXIOBASE describes every product in every region, including products a region barely
makes. Where a region's output of a product is tiny, the emissions the table attributes to
it rest on very little data, and the intensity — emissions per euro of output — can be
many times what any other region shows. Such a cell is harmless while nothing touches it,
and wrong by the same factor as soon as a tape or a step of the baseline walk scales it up.

This job reads the cached baseline and, for every product, compares each region's direct
intensity with the output-weighted world intensity of that product. It writes
``data/baseline/intensity_outliers.csv``: one row for each region and product whose
intensity is more than ``OUTLIER_FACTOR`` times above or below the world figure, with how
much output and emissions the cell holds, so that a large, real difference (a coal-heavy
grid) can be told from a small-sample artefact.

It changes nothing in the model. It says where to look.

Run with ``just diagnose-intensities``. Needs the cached baseline (``just baseline``).

References:
  - docs/design/baseline_walk.md — "Which regions can describe which products"
  - docs/backlog.md — geothermal's 211 g CO2e/kWh, the first such cell found by hand
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pymrio

from redworlds.config import load_config
from redworlds.engine.io_tables import GHG_EXTENSION, GHG_STRESSOR
from redworlds.jobs.build_baseline import BASELINE_NAME
from redworlds.jobs.prepare_electricity import BASELINE_DATA, write_with_header

OUTLIER_FACTOR: float = 5.0
# A region making under this share of the world's output of a product is a small sample.
SMALL_SHARE: float = 0.01
KG_PER_TONNE: float = 1_000.0


def intensity_table(output: pd.Series, emissions: pd.Series) -> pd.DataFrame:
    """Compare each region's intensity for each product with the world's.

    Args:
        output: Money output indexed by (region, product).
        emissions: Direct emissions of the same cells, in any one unit.

    Returns:
        One row per (region, product) with positive world output: ``output``,
        ``emissions``, ``intensity`` (emissions per unit of output), ``world_intensity``
        (output-weighted across regions), ``ratio`` of the two, and ``output_share`` and
        ``emissions_share`` of the world total for that product.
    """
    table = pd.DataFrame({"output": output, "emissions": emissions})
    table.index = table.index.set_names(["region", "product"])
    world = table.groupby(level="product").sum()
    table = table.join(world.add_prefix("world_"), on="product")
    table = table[(table["world_output"] > 0.0) & (table["output"] > 0.0)].copy()
    table["intensity"] = table["emissions"] / table["output"]
    table["world_intensity"] = table["world_emissions"] / table["world_output"]
    table["ratio"] = table["intensity"] / table["world_intensity"].replace(0.0, np.nan)
    table["output_share"] = table["output"] / table["world_output"]
    table["emissions_share"] = table["emissions"] / table["world_emissions"].replace(0.0, np.nan)
    return table.drop(columns=["world_output", "world_emissions"]).reset_index()


def flag_outliers(
    table: pd.DataFrame,
    outlier_factor: float = OUTLIER_FACTOR,
    small_share: float = SMALL_SHARE,
) -> pd.DataFrame:
    """Keep the cells whose intensity is far from the world's, and say which are small samples.

    A cell is an outlier when its intensity is more than ``outlier_factor`` times above or
    below the world intensity. ``small_sample`` marks the outliers where the region makes
    under ``small_share`` of the world's output of the product: those are the ones most
    likely to be artefacts rather than real differences between regions.
    """
    far = (table["ratio"] > outlier_factor) | (table["ratio"] < 1.0 / outlier_factor)
    outliers = table[far & table["ratio"].notna()].copy()
    outliers["small_sample"] = outliers["output_share"] < small_share
    return outliers.sort_values(["small_sample", "emissions"], ascending=[True, False]).reset_index(drop=True)


def main() -> None:
    """Write the outlier table for the cached baseline and print a summary."""
    world = pymrio.load_all(Path(load_config()["data"]["worlds_path"]) / BASELINE_NAME)
    assert world.x is not None
    emissions = getattr(world, GHG_EXTENSION).F.loc[GHG_STRESSOR] / KG_PER_TONNE
    table = intensity_table(world.x["indout"], emissions)
    outliers = flag_outliers(table)

    columns = ["region", "product", "output", "emissions", "intensity", "world_intensity", "ratio"]
    columns += ["output_share", "emissions_share", "small_sample"]
    rounded = outliers[columns].round(
        {
            "output": 1,
            "emissions": 0,
            "intensity": 2,
            "world_intensity": 2,
            "ratio": 2,
            "output_share": 4,
            "emissions_share": 4,
        }
    )
    write_with_header(
        rounded,
        BASELINE_DATA / "intensity_outliers.csv",
        "Region and product cells of the 2011 baseline whose direct greenhouse-gas intensity is\n"
        f"more than {OUTLIER_FACTOR:g} times above or below the world intensity for that product.\n"
        "output in million EUR (2011); emissions in tonnes CO2e; intensity in tonnes per\n"
        f"million EUR. small_sample: the region makes under {SMALL_SHARE:.0%} of world output of the product.\n"
        "Derived from EXIOBASE 3.8.2 (CC BY-SA 4.0) by redworlds.jobs.diagnose_intensities.\n"
        "Do not edit by hand; re-run the job.",
    )

    total = table["emissions"].sum()
    small = outliers[outliers["small_sample"]]
    large = outliers[~outliers["small_sample"]]
    small_held = small["emissions"].sum() / total
    large_held = large["emissions"].sum() / total
    print(f"{len(table):,} region-product cells with output; {len(outliers):,} are far from the world intensity.")
    print(f"  small samples: {len(small):,} cells holding {small_held:.2%} of world emissions")
    print(f"  not small:     {len(large):,} cells holding {large_held:.2%} of world emissions")
    print("\nOutliers per region (small sample / not small):")
    counts = outliers.groupby(["region", "small_sample"]).size().unstack(fill_value=0)
    print(counts.to_string())
    pd.set_option("display.width", 220)
    pd.set_option("display.max_colwidth", 46)
    print("\nLargest outliers by emissions:")
    print(
        rounded.sort_values("emissions", ascending=False)
        .head(15)[["region", "product", "emissions", "ratio", "output_share"]]
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
