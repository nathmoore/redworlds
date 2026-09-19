# Red Worlds

[![PyPI version](https://img.shields.io/pypi/v/redworlds.svg)](https://pypi.org/project/redworlds/)
[![CI](https://github.com/nathmoore/redworlds/actions/workflows/ci.yml/badge.svg)](https://github.com/nathmoore/redworlds/actions/workflows/ci.yml)
[![Docs](https://github.com/nathmoore/redworlds/actions/workflows/docs.yml/badge.svg)](https://nathmoore.github.io/redworlds/)
[![License: CC BY-SA 4.0](https://img.shields.io/badge/License-CC_BY--SA_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by-sa/4.0/)

**Red Worlds is the open-source engine behind Red Carbon** — a web game about
decarbonisation, economics, and an uncomfortable question sitting just below the surface:
*is climate change actually controllable?*

It is a **data engine**. When the game says an intervention saved a certain amount of
carbon, that figure is computed rather than asserted. This repo is that layer only — not
the game.

Being computed does not make it true. A model is a set of arguments about how the world
fits together, and ours can be read, checked and disagreed with. That is why it is here.

---

## How it works

The game is set in 2050. A player picks one large-scale intervention in one of seven
world regions, and Red Worlds answers: *how much carbon does that avoid, over the fifty
years to 2100, compared with not doing it?*

That last clause matters more than anything else here. Every number this engine produces
is a **difference against a baseline**, not a forecast of the world in 2050.

### The method, in one idea

Every purchase drags a chain of production behind it. A solar panel needs steel; steel
needs coal; coal needs machinery; machinery needs steel again. **Input–output analysis**
is the standard way of solving that loop — a table of who buys what from whom across a
whole economy, arranged so you can ask what a change in demand does to total output, and
then to total emissions.

The table we use is [EXIOBASE](https://www.exiobase.eu/): around 200 product categories
across 49 countries and regions, with physical accounts for CO₂ and other greenhouse
gases attached. It was built by a European research consortium and its method is set out
in a [peer-reviewed paper](https://doi.org/10.1111/jiec.12715). It is a serious, widely
used dataset. It is also a model of an economy in **2011**, with everything that implies.

### The three wings

Every intervention is one of three kinds. They differ in **what happens to the money**,
and that turns out to decide the answer.

**BUILD — construct new low-carbon capacity**, say a ten-reactor nuclear block. The money
is *moved*: redirected into investment, which means concrete, steel, machinery and
electrical equipment, all emitting now, years before the thing generates anything. So
emissions rise before they fall — the J-curve. How big that hump is against how deep the
eventual fall goes is the whole argument about building your way out.

**SWAP — substitute one product for another** at the same volume, motor fuel for
electricity in cars. The money is *kept*: a household spending less on petrol spends it
on something else, which has a footprint of its own. That re-spend is the **rebound**, and
we model it deliberately. Leaving it out is the commonest way to flatter a swap.

**REDUCE — consume less of a basket of products.** The money *leaves the model*. The
economy shrinks in proportion and there is no rebound at all. That is a post-growth
framing and a real choice, not a neutral default — see below.

### Scoring

The engine takes the annual difference against the baseline, spreads it across the fifty
years through a deployment curve — things arrive gradually, not all at once — and sums
the result. The game sizes every intervention to the same expected abatement; Red Worlds
answers how much of each one that takes, in each region.

---

## What we assume, and where it breaks

The part worth reading slowly, and the reason this is open.

- **The base year is 2011**, the last complete table in EXIOBASE 3.8.2. We walk it forward
  to 2050 on an SSP2 pathway. Economies change in forty years; ours changes only in the
  ways we have modelled.
- **Trade patterns are fixed and prices do not respond.** Demand-driven input–output
  models have no market clearing: nothing gets dearer because you bought more of it.
  Standard, and a real limit.
- **Forty-nine regions are squashed into seven** — legibility bought with resolution.
- **REDUCE's missing rebound is the most contestable assumption in the engine.** Money not
  spent leaves entirely. You could argue it is saved, invested, or spent elsewhere, and
  each gives a different answer. We chose the post-growth reading, wrote down why, and
  labelled it so you can find it and object.
- **Plenty is outside this table** — land use, forestry, physical constraints. An
  intervention the model cannot see is not one the model has disproved.

The full list with the reasoning for each is in
[docs/design/assumptions.md](docs/design/assumptions.md). If you think one is wrong, that
is a conversation we would rather have in the open:
[raise an issue](https://github.com/nathmoore/redworlds/issues).

**Why it is public.** Red Carbon is a game about people disagreeing over what to do about
climate change, and that only works if the disagreement is honest — not overstating what
an intervention achieves, not pretending a hard trade-off is easy, not hiding the
assumption doing the heavy lifting. So the engine is open and the assumptions are in
plain language. If you arrived sceptical, follow the assumptions rather than the
conclusions. That is the right instinct, and this repo is built for it.

---

## Explore it with an AI

This repository is written to be read by an assistant. Paste its address into Claude,
ChatGPT, Gemini, Copilot or whatever you use, with *"read this repository and help me
understand it"*:

```
https://github.com/nathmoore/redworlds
```

Then ask — *"is the science here real, or made up for a game?"*, *"why does a BUILD
intervention make emissions rise before they fall?"*, *"take me through how I'd model
halving a region's cement use, one decision at a time"*.

One thing to know first: an assistant can explain the method, but **it cannot give you a
number**. Numbers come from running the engine, which needs a 1.9 GB download and a few
minutes of computation. A confident figure in tonnes that arrived without a run was
invented.

[**docs/ai-guide.md**](docs/ai-guide.md) goes further — a glossary, a method for taking a
modelling decision apart step by step, how to get a coding assistant to run EXIOBASE with
you, and the five mistakes assistants reliably make here.

---

## Learn more

| | |
|---|---|
| Why the model does what it does, and its limits | [assumptions.md](docs/design/assumptions.md) |
| How the pieces fit together | [architecture.md](docs/design/architecture.md) |
| BUILD, SWAP and REDUCE in technical detail | [game_mechanics.md](docs/design/game_mechanics.md) |
| What the game requires of the engine | [red_carbon_contract.md](docs/design/red_carbon_contract.md) |
| What is built, in progress, or undecided | [backlog.md](docs/backlog.md) |
| Worked examples you can run | [examples/](examples/) |
| Where the data comes from and how to get it | [data/README.md](data/README.md) |

On the method itself: [pymrio](https://pymrio.readthedocs.io/), the library doing the
table maths, has a good tutorial introduction to input–output analysis; David MacKay's
[Sustainable Energy — Without the Hot Air](https://www.withouthotair.com/) is free online
and still the clearest book written on sizing climate interventions honestly. Full
bibliography: [docs/references.md](docs/references.md).

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

The default tests need no data, so a fresh clone proves itself in under a minute. The
baseline build, the integration tests and the notebooks need the real EXIOBASE download
(~1.9 GB — see [data/README.md](data/README.md)) and a `config/config.toml` copied from
`config/config.example.toml`:

```bash
just baseline              # build and cache the 2050 baseline world — minutes, not seconds
just test -m integration   # the tests that use real data
```

Before changing anything, read [AGENTS.md](AGENTS.md) — the working agreement for this
repo, written for human and AI contributors alike. Contributions welcome:
[CONTRIBUTING.md](CONTRIBUTING.md).

---

## License

**CC BY-SA 4.0**, matching EXIOBASE v3.8, the data this engine is built on. Use, share and
adapt freely, including commercially, provided you credit and share alike. See
[LICENSE](LICENSE). EXIOBASE 3.8.2 (Stadler et al. 2021) is CC BY-SA 4.0; the capital use
matrices (Wood & Södersten 2021) are CC BY 4.0. Full citations:
[docs/references.md](docs/references.md).

Created in 2026 by [Nathan Moore](https://github.com/nathmoore). Built from the
[audreyfeldroy/cookiecutter-pypackage](https://github.com/audreyfeldroy/cookiecutter-pypackage) template.
