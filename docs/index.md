# Red Worlds

Open source Python engine for [Red Carbon](https://github.com/nathmoore/red-carbon) —
a game about decarbonisation, economics, and climate action.

## Start here — by audience

| I want to... | Go to |
|---|---|
| Understand how the engine works | [Architecture](design/architecture.md) |
| Explore the game design assumptions | [Assumptions](design/assumptions.md) |
| Understand BUILD, SWAP, REDUCE mechanics | [Game Mechanics](design/game_mechanics.md) |
| See what the game requires of the engine | [Red Carbon Contract](design/red_carbon_contract.md) |
| See what is being worked on and what is undecided | [Backlog](backlog.md) |
| Try the IO table examples / run notebooks | [examples/](https://github.com/nathmoore/redworlds/tree/main/examples) |
| Understand the data sources | [Data Guide](https://github.com/nathmoore/redworlds/blob/main/data/README.md) |
| Set up locally / contribute code | [Installation](installation.md) · [Contributing](https://github.com/nathmoore/redworlds/blob/main/CONTRIBUTING.md) |
| Browse the Python API | [API Reference](api.md) |
| Find citations and data sources | [References](references.md) |

## What this project does

Each day a Red Carbon player plays one large-scale intervention (a "tape") in 2050.
Red Worlds applies it to an [EXIOBASE](https://www.exiobase.eu/) input-output world and
returns the cumulative CO₂ abated over 2050–2100.

The three action types:

- **BUILD** — construct new low-carbon capacity; CapEx spread over a build period
- **SWAP** — shift a fraction of one technology's demand to a cleaner alternative
- **REDUCE** — consume less of a basket of products (no economic rebalancing — post-growth by design)

See [Game Mechanics](design/game_mechanics.md) for the full technical contracts,
and [Assumptions](design/assumptions.md) for the rationale behind each design choice.
