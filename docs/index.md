# Red Worlds

Open source Python engine for [Red Carbon](https://github.com/nathmoore/red-carbon) —
a game about decarbonisation, economics, and climate action.

## Start here — by audience

| I want to... | Go to |
|---|---|
| Understand how the engine works | [Architecture](design/architecture.md) |
| Explore the game design assumptions | [Assumptions](design/assumptions.md) |
| Understand BUILD, SWAP, REDUCE mechanics | [Game Mechanics](design/game_mechanics.md) |
| Try the IO table examples / run notebooks | [examples/](https://github.com/nathmoore/redworlds/tree/main/examples) |
| Understand the data sources | [Data Guide](https://github.com/nathmoore/redworlds/blob/main/data/README.md) |
| Set up locally / contribute code | [Installation](installation.md) · [Contributing](https://github.com/nathmoore/redworlds/blob/main/CONTRIBUTING.md) |
| Browse the Python API | [API Reference](api.md) |
| Find citations and data sources | [References](design/references.md) |

## What this project does

Each player in Red Carbon has their own simulated world, represented as an
[EXIOBASE](https://www.exiobase.eu/) input-output (IO) table.
Red Worlds applies the player's daily action to their world and returns updated
emissions figures.

The three action types:

- **BUILD** — construct new low-carbon capacity; CapEx spread over a build period
- **SWAP** — shift a fraction of one technology's demand to a cleaner alternative
- **REDUCE** — reduce consumption of a sector (no economic rebalancing — post-growth by design)

See [Game Mechanics](design/game_mechanics.md) for the full technical contracts,
and [Assumptions](design/assumptions.md) for the rationale behind each design choice.
