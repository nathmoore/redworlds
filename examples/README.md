# Examples

Jupyter notebooks that walk through how the Red Worlds engine works, how the
IO tables are constructed, and how you can run your own scenarios.

These are aimed at data-curious players, researchers, and anyone who wants
to understand the science behind Red Carbon.

---

## EXIOBASE: what you need and where to get it

Red Worlds is built on **EXIOBASE 3.8.2**, a global multi-regional input-output
database. We use the 2011 product-by-product tables (`IOT_2011_pxp.zip`).

**Why 2011?** It is the latest year in 3.8.2 with complete, non-extrapolated
supply-use tables. Red Worlds extrapolates from 2011 along an SSP2 pathway to the
in-game year of 2050, and on to 2100 for the baseline trajectory.

**Why version 3.8.2 specifically?** It is the last release under the
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) licence, which
allows open-source use with attribution. More recent releases include "now-casted"
years and use CC BY 4.0 (no ShareAlike requirement) — fine for personal and research
use, but check the terms before redistribution.

### Download

Download `IOT_2011_pxp.zip` from Zenodo:

> **https://zenodo.org/records/5589597**

Extract into `data/exiobase/` (this directory is gitignored — the files are large
and licensed separately from this repo).

Please cite EXIOBASE as:

> Stadler, K., Wood, R., Bulavskaya, T., Södersten, C.-J., Simas, M., Schmidt, S.,
> Usubiaga, A., Acosta-Fernández, J., Kuenen, J., Bruckner, M., Giljum, S., Lutter, S.,
> Merciai, S., Schmidt, J. H., Theurl, M. C., Plutzar, C., Kastner, T., Eisenmenger, N.,
> Erb, K.-H., … Tukker, A. (2021). EXIOBASE 3 (3.8.2) [Data set]. Zenodo.
> https://doi.org/10.5281/zenodo.5589597

### A note on monetary units

EXIOBASE values are in **2011 million EUR at basic prices**. Basic prices are
producer prices — what the seller receives — excluding taxes on products and
excluding trade and transport margins (roughly: "price at the factory gate, before
VAT or shipping"). Red Worlds converts these internally to **2026 constant million USD**
for all player-facing monetary figures (see `engine/currency.py`).

### A note on regions

EXIOBASE covers ~49 countries and regions. Red Worlds aggregates these into **7
game regions** for legibility. Our calculations are therefore slightly less granular
than results you would get running EXIOBASE at full country resolution. The mapping
is in `data/concordances/region_mapping.csv`.

---

## How to run the notebooks

```bash
# Install dependencies (including Jupyter)
uv sync --group docs

# Start JupyterLab
uv run jupyter lab
```

Or open the notebooks in VS Code with the Jupyter extension.

---

## Notebooks

| Notebook | What it covers |
|----------|---------------|
| [01_build_io_tables.ipynb](01_build_io_tables.ipynb) | How to download EXIOBASE, load it with pymrio, and build the baseline IO tables used by Red Worlds |
| [02_sample_payloads.ipynb](02_sample_payloads.ipynb) | Sample BUILD/SWAP/REDUCE JSON payloads from Red Carbon, example result JSON, and manual action testing |

More notebooks are planned — contributions welcome.

---

## Using this repo with an AI assistant

The [`prompts/`](prompts/) folder contains context files you can paste into an AI
conversation (Claude.ai, ChatGPT, Copilot, etc.) to get scientifically grounded
answers to carbon modelling questions.

Start with [`prompts/red_worlds_context.md`](prompts/red_worlds_context.md) — it
orients the AI to the project's assumptions, data structures, and current
implementation status. Example questions you can then ask:

- "Walk me through what happens in the IO tables when a player reduces steel demand by 10%."
- "Which EXIOBASE sectors would shift if a region swaps 20% of gas heating for heat pumps?"
- "What are the known limitations of this model?"

The AI will explain methodology and help you understand the science. For actual
numbers it will need the engine to be run against real EXIOBASE data.

---

## Want to contribute a notebook?

If you've done something interesting with the Red Worlds engine or EXIOBASE,
we'd love to include it here. See [CONTRIBUTING.md](../CONTRIBUTING.md).
