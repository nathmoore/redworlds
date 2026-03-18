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
| Try the IO table examples or run notebooks | [examples/](examples/) |
| Understand the data sources and concordances | [data/README.md](data/README.md) |
| Contribute code or raise an issue | [CONTRIBUTING.md](CONTRIBUTING.md) |
| Integrate with the Red Carbon WordPress site | [docs/api.md](docs/api.md) *(TBC)* |

---

## What this project does

Each player in Red Carbon has their own simulated world, represented as an [EXIOBASE](https://www.exiobase.eu/) input-output (IO) table living on a remote server. Red Worlds handles:

1. **Overnight preparation** — economic growth and population updates are applied to advance the world one simulation year.
2. **Scenario generation** — a daily scenario is created from a target emissions category (e.g. *European residential heating*), mapped to EXIOBASE sectors via concordance tables in this repo.
3. **Player actions** — the player interacts with the scenario via the Red Carbon Decarbonator Deck, choosing one of three approaches:
   - **BUILD** — construct new low-carbon capacity (e.g. wind farms, nuclear). CapEx is spread over a build period; the energy mix shifts after completion.
   - **SWAP** — replace a fraction of an existing technology with a cleaner alternative (e.g. heat pumps replacing gas boilers). The IO mix is shifted proportionally.
   - **REDUCE** — reduce consumption of a sector (e.g. lower thermostat settings). The IO demand is reduced; unlike BUILD and SWAP, the economy is *not* rebalanced (a deliberate post-growth design choice).

All calculations update the player's EXIOBASE-derived IO tables, recalculating emissions at each step.

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
