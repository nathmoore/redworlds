# Red Worlds

[![PyPI version](https://img.shields.io/pypi/v/redworlds.svg)](https://pypi.org/project/redworlds/)
[![CI](https://github.com/nathmoore/redworlds/actions/workflows/ci.yml/badge.svg)](https://github.com/nathmoore/redworlds/actions/workflows/ci.yml)
[![Docs](https://github.com/nathmoore/redworlds/actions/workflows/docs.yml/badge.svg)](https://nathmoore.github.io/redworlds/)
[![License: CC BY-SA 4.0](https://img.shields.io/badge/License-CC_BY--SA_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by-sa/4.0/)

**Red Worlds is the open-source engine behind Red Carbon** — a web game about
decarbonisation, economics, and an uncomfortable question sitting just below the surface:
*is climate change actually controllable?*

It is a **data engine**. When the game tells you an intervention saved a certain amount of
carbon, that number is not a guess or a designer's opinion — it comes out of
[EXIOBASE](https://www.exiobase.eu/), a global economic dataset used by academic
researchers and cited by the IPCC, run through standard input–output methods. This repo is
that layer and only that layer. It is not the game; the game's front end lives elsewhere.

You do not need to be a programmer to look inside it. Two ways in, below.

---

## Explore this with an AI

The fastest way into this project is to hand it to an assistant and start asking. This
repository is written to be read that way — plain-language documents explaining what the
model does, what it assumes, and what it deliberately ignores.

**How:** copy this repository's address and paste it into Claude, ChatGPT, Gemini,
Copilot or whatever you already use, with something like *"read this repository and help
me understand it"*.

```
https://github.com/nathmoore/redworlds
```

Nothing to install, no account needed here, nothing to download. Then ask it anything
below — or your own version of it.

### If you are new to all of this

> "What is this project, in plain English?"

> "Is the science behind this real, or is it made up for a game?"

> "What is an input–output model, and why would you use one to answer a question about
> carbon?"

> "Where does the underlying data come from, and who else uses it?"

> "The game is set in 2050 but the data is from 2011. How does that work, and is it
> honest?"

> "What does this model get wrong, or deliberately leave out?"

### If you want to understand how it works

> "Walk me through what happens in the tables when someone cuts a basket of consumer
> goods by 1.4%, and why it matters that the money leaves the model."

> "Which product categories would I need to change to model eleven million cars moving
> from petrol to electricity, and where does the rebound effect show up?"

> "Why does a BUILD intervention make emissions rise before they fall, and what decides
> how big that hump is?"

> "Why does counting capital goods properly change the answer for a consumer-spending
> intervention?"

> "Explain the difference between BUILD, SWAP and REDUCE as economics, not as game
> mechanics."

### If you want to work something out

> "I want to know what would happen if a region halved its cement use. Take me through
> how I'd model that here, one decision at a time, and tell me where you're least sure."

> "Is this intervention even expressible in this kind of model? If not, what would it
> take?"

> "What's the largest version of this intervention that's physically plausible in this
> region?"

> "Find the papers in this repo's references that establish the method for what I'm
> describing."

### What it can answer, and what it can't

An assistant that has read this repository can explain the method, the assumptions and
the reasoning, and can walk you through what *would* happen under a given intervention.

It cannot give you a number. Numbers come from running the engine, which needs a 1.9 GB
data download and a few minutes of computation. **If an assistant hands you a confident
figure in tonnes without having run anything, it made the figure up.** That is the single
most useful thing to know before you start.

Two other things worth holding: the authoritative documents are
[docs/design/assumptions.md](docs/design/assumptions.md) (why the model does what it does)
and [docs/design/red_carbon_contract.md](docs/design/red_carbon_contract.md) (what the game
requires of it) — if an answer contradicts those, they win. And parts of this engine are
deliberately unbuilt, so an assistant may describe something as working when it is still a
stub. [docs/backlog.md](docs/backlog.md) is the honest current state.

### Going further

If you use a coding assistant that can run things — Claude Code, Codex, Cursor and the
like — it can do more than explain: clone this repo and it can run the tests, build the
baseline world and try a scenario alongside you.
[docs/ai-guide.md](docs/ai-guide.md) covers that, plus a glossary, a method for taking a
modelling decision apart one step at a time, and the five mistakes assistants reliably
make here.

---

## Prefer to read it yourself?

No AI required. Start with whichever of these matches what you want.

**The data and method**

- [EXIOBASE](https://www.exiobase.eu/) — the global economic dataset underneath everything here
- [The 3.8.2 release on Zenodo](https://doi.org/10.5281/zenodo.5589597) — the exact version used, and its citation
- [Stadler et al. 2018](https://doi.org/10.1111/jiec.12715) — the peer-reviewed paper describing how EXIOBASE is built
- [pymrio](https://pymrio.readthedocs.io/) — the Python library that handles the table maths, with its own tutorials on input–output analysis

**The wider idea**

- [Sustainable Energy — Without the Hot Air](https://www.withouthotair.com/), David MacKay — free online, and the clearest book ever written on sizing climate interventions honestly. Numbers, not adjectives.

**This project**

- [The documentation site](https://nathmoore.github.io/redworlds/) — the same docs as this repo, rendered and searchable
- [docs/design/assumptions.md](docs/design/assumptions.md) — every design decision and why, including the known limitations
- [docs/references.md](docs/references.md) — the full bibliography

---

## Start here — by audience

| I want to... | Go to |
|---|---|
| Understand how the engine works | [docs/design/architecture.md](docs/design/architecture.md) |
| Explore the modelling assumptions and their limits | [docs/design/assumptions.md](docs/design/assumptions.md) |
| Understand BUILD, SWAP, REDUCE mechanics | [docs/design/game_mechanics.md](docs/design/game_mechanics.md) |
| See what the game requires of the engine | [docs/design/red_carbon_contract.md](docs/design/red_carbon_contract.md) |
| See what is being worked on and what is undecided | [docs/backlog.md](docs/backlog.md) |
| Try the IO table examples or run notebooks | [examples/](examples/) |
| Understand the data sources and concordances | [data/README.md](data/README.md) |
| Work on this repo, with or without an AI | [AGENTS.md](AGENTS.md) |
| Browse the Python API | [the docs site](https://nathmoore.github.io/redworlds/api/) |
| Contribute code or raise an issue | [CONTRIBUTING.md](CONTRIBUTING.md) |

---

## What this project does

The game is set in 2050. Each day a player plays one large-scale intervention (a "tape")
in one of seven world regions, and Red Worlds scores it as **cumulative CO₂ abated over
2050–2100** against a do-nothing baseline. Red Worlds handles:

1. **The baseline** — a one-off job extrapolates the 2011 EXIOBASE table to a 2050 world
   along an SSP2 pathway, with capital endogenised, and caches the result. Building it
   takes minutes; loading the cache takes seconds.
2. **The three wings** — every tape belongs to one, and they differ in what happens to
   the money:
   - **BUILD** — construct new low-carbon capacity (say, a ten-reactor nuclear block).
     Capital expenditure is injected into investment during the build years, so the curve
     rises before it falls; after completion the electricity mix shifts. *The money moves.*
   - **SWAP** — substitute one product for another at the same volume (motor fuel for
     electricity in cars). Total spend is preserved and the re-spend is a deliberate
     rebound. *The money stays.*
   - **REDUCE** — consume less of a basket of products. The spend leaves the model and
     the economy shrinks in proportion, with no rebound — a deliberate post-growth design
     choice. *The money goes.*
3. **Scoring** — the annual emissions difference against the baseline, spread across the
   fifty years through a deployment curve.

Because every player-facing shock is linear in how much of the intervention gets
deployed, each tape is solved **once, offline**, and ships to the game as a small table of
numbers. There is no live server in the loop.

The game sizes every tape to the same expected abatement; Red Worlds answers how much of
each intervention that takes, in each region. What the game requires of the engine is
written down in [docs/design/red_carbon_contract.md](docs/design/red_carbon_contract.md).

---

## Quickstart (for developers)

```bash
git clone https://github.com/nathmoore/redworlds.git
cd redworlds
uv sync
just qa          # format, lint, type-check, test
just test        # tests only — uses pymrio's built-in test world, no EXIOBASE needed
just docs-serve  # live docs at http://localhost:8000
```

The default test suite needs no data at all, so a fresh clone proves itself in under a
minute. Everything beyond that — the integration tests, the baseline build, the
notebooks — needs the real EXIOBASE download (~1.9 GB, instructions in
[data/README.md](data/README.md)) and a `config/config.toml` copied from
`config/config.example.toml`:

```bash
just baseline              # build and cache the 2050 baseline world — minutes, not seconds
just test -m integration   # the tests that use real data
```

Before changing anything, read [AGENTS.md](AGENTS.md) — the working agreement for this
repo, written for human and AI contributors alike.

---

## License

Red Worlds is licensed under **Creative Commons Attribution-ShareAlike 4.0 International
(CC BY-SA 4.0)**, matching the license of EXIOBASE v3.8, the data this engine is built on.

This means you are free to use, share, and adapt this work — including for commercial
purposes — provided you give appropriate credit and distribute any adaptations under the
same license.

See [LICENSE](LICENSE) for the full text, or visit
[creativecommons.org/licenses/by-sa/4.0](https://creativecommons.org/licenses/by-sa/4.0/).

Data used by the engine and its licences (full citations in
[docs/references.md](docs/references.md)):

| Data | Licence |
|---|---|
| EXIOBASE 3.8.2 (Stadler et al. 2021) | CC BY-SA 4.0 |
| Capital use matrices for EXIOBASE 3.8.2 (Wood & Södersten 2021) | CC BY 4.0 |

---

## About

Red Worlds was created in 2026 by [Nathan Moore](https://github.com/nathmoore).
Built from the [audreyfeldroy/cookiecutter-pypackage](https://github.com/audreyfeldroy/cookiecutter-pypackage) template.
