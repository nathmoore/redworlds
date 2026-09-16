# Red Worlds

[![PyPI version](https://img.shields.io/pypi/v/redworlds.svg)](https://pypi.org/project/redworlds/)
[![CI](https://github.com/nathmoore/redworlds/actions/workflows/ci.yml/badge.svg)](https://github.com/nathmoore/redworlds/actions/workflows/ci.yml)
[![Docs](https://github.com/nathmoore/redworlds/actions/workflows/docs.yml/badge.svg)](https://nathmoore.github.io/redworlds/)
[![License: CC BY-SA 4.0](https://img.shields.io/badge/License-CC_BY--SA_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by-sa/4.0/)

**Red Worlds is the open-source Python engine behind [Red Carbon](https://github.com/nathmoore/red-carbon)** — a web game about decarbonisation, economics, and an uncomfortable question that sits just below the surface: *is climate change actually controllable?*

This repo is the science and simulation layer only. It is not the game itself. The game's WordPress front end lives in a separate private repo.

---

## Start here — by audience

| I want to... | Go to |
|---|---|
| Understand how the engine works | [docs/design/architecture.md](docs/design/architecture.md) |
| Explore the game design assumptions | [docs/design/assumptions.md](docs/design/assumptions.md) |
| Understand BUILD, SWAP, REDUCE mechanics | [docs/design/game_mechanics.md](docs/design/game_mechanics.md) |
| See what the game requires of the engine | [docs/design/red_carbon_contract.md](docs/design/red_carbon_contract.md) |
| See what is being worked on and what is undecided | [docs/backlog.md](docs/backlog.md) |
| Try the IO table examples or run notebooks | [examples/](examples/) |
| Understand the data sources and concordances | [data/README.md](data/README.md) |
| Contribute code or raise an issue | [CONTRIBUTING.md](CONTRIBUTING.md) |
| Integrate with the Red Carbon WordPress site | [docs/api.md](docs/api.md) *(TBC)* |

---

## What this project does

The game is set in 2050. Each day a player plays one large-scale intervention (a "tape") in one of seven world regions, and Red Worlds scores it as **cumulative CO₂ abated over 2050–2100** against a do-nothing baseline built from [EXIOBASE](https://www.exiobase.eu/), a global input-output (IO) model of the economy. Red Worlds handles:

1. **The baseline** — a one-off job extrapolates the 2011 EXIOBASE table to a 2050 world along an SSP2 pathway, with capital endogenised, and caches it.
2. **The three wings** — every tape belongs to one:
   - **BUILD** — construct new low-carbon capacity (e.g. a 10-reactor nuclear block). Capex is injected into investment during the build years, so the curve rises before it falls; after completion the electricity mix shifts.
   - **SWAP** — substitute one product for another at the same volume (e.g. motor fuel for electricity in cars). Total spend is preserved; the re-spend is a deliberate rebound.
   - **REDUCE** — consume less of a basket of products. The spend leaves the model and the economy shrinks in proportion, with no rebound (a deliberate post-growth design choice).
3. **Scoring** — the annual emissions difference against the baseline, spread across the fifty years through a deployment curve.

The game sizes every tape to the same expected abatement; Red Worlds answers how much of each intervention that takes in each region. What the game requires of the engine is written down in [docs/design/red_carbon_contract.md](docs/design/red_carbon_contract.md).

---

## Quickstart (for developers)

```bash
git clone https://github.com/nathmoore/redworlds.git
cd redworlds
uv sync
just qa          # format, lint, type-check, test
just test        # tests only (uses pymrio built-in test IO — no EXIOBASE needed)
just docs-serve  # live docs at http://localhost:8000
```

To run integration tests against real EXIOBASE data, first configure `config/config.toml` (copy from `config/config.example.toml`), then:

```bash
just test -m integration
```

---

## License

Red Worlds is licensed under **Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)**, matching the license of EXIOBASE v3.8, the data this engine is built on.

This means you are free to use, share, and adapt this work — including for commercial purposes — provided you give appropriate credit and distribute any adaptations under the same license.

See [LICENSE](LICENSE) for the full text, or visit [creativecommons.org/licenses/by-sa/4.0](https://creativecommons.org/licenses/by-sa/4.0/).

---

## About

Red Worlds was created in 2026 by [Nathan Moore](https://github.com/nathmoore).
Built from the [audreyfeldroy/cookiecutter-pypackage](https://github.com/audreyfeldroy/cookiecutter-pypackage) template.
