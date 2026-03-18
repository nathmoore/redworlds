# Examples

Jupyter notebooks that walk through how the Red Worlds engine works, how the
IO tables are constructed, and how you can run your own scenarios.

These are aimed at data-curious players, researchers, and anyone who wants
to understand the science behind Red Carbon.

---

## How to run the notebooks

You'll need EXIOBASE downloaded first for most notebooks. See [data/README.md](../data/README.md).

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

## Want to contribute a notebook?

If you've done something interesting with the Red Worlds engine or EXIOBASE,
we'd love to include it here. See [CONTRIBUTING.md](../CONTRIBUTING.md).
