# Red Worlds

Open-source Python engine for **Red Carbon**, a game about decarbonisation, economics,
and climate action.

It is a **data engine**: the carbon numbers the game reports are computed rather than
asserted, from [EXIOBASE](https://www.exiobase.eu/) — a global economic dataset built by a
European research consortium — run through standard input–output methods. This is that
layer only, not the game itself.

> *All models are wrong, but some are useful.* — George Box

Which is why the method, the assumptions and the judgement calls are all written down in
plain language. [Assumptions](design/assumptions.md) is the place to start.

## Start here — by audience

| I want to... | Go to |
|---|---|
| Explore this project with an AI assistant | [Explore with an AI](ai-guide.md) |
| Understand how the engine works | [Architecture](design/architecture.md) |
| Explore the modelling assumptions and their limits | [Assumptions](design/assumptions.md) |
| Understand BUILD, SWAP, REDUCE mechanics | [Game Mechanics](design/game_mechanics.md) |
| See what the game requires of the engine | [Red Carbon Contract](design/red_carbon_contract.md) |
| See what is being worked on and what is undecided | [Backlog](backlog.md) |
| Try the IO table examples / run notebooks | [examples/](https://github.com/nathmoore/redworlds/tree/main/examples) |
| Understand the data sources | [Data Guide](https://github.com/nathmoore/redworlds/blob/main/data/README.md) |
| Set up locally / contribute code | [Installation](installation.md) · [Working agreement](https://github.com/nathmoore/redworlds/blob/main/AGENTS.md) |
| Browse the Python API | [API Reference](api.md) |
| Find citations and data sources | [References](references.md) |

## What this project does

Each day a Red Carbon player plays one large-scale intervention (a "tape") in 2050.
Red Worlds applies it to an EXIOBASE input-output world and returns the cumulative CO₂
abated over 2050–2100, against a baseline in which nothing was done.

The three action types differ in what happens to the money:

- **BUILD** — construct new low-carbon capacity; capital expenditure spread over a build
  period, then the electricity mix shifts. *The money moves.*
- **SWAP** — shift a fraction of one technology's demand to a cleaner alternative, at the
  same total spend. *The money stays, and the re-spend is a real rebound.*
- **REDUCE** — consume less of a basket of products; the economy shrinks in proportion.
  *The money leaves the model* — post-growth by design.

See [Game Mechanics](design/game_mechanics.md) for the full technical contracts,
and [Assumptions](design/assumptions.md) for the rationale behind each design choice.
