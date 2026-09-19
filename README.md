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

> *All models are wrong, but some are useful.*
> — George Box

Which is why everything here is written down in plain language: the method, the
assumptions, and the judgement calls that could have gone another way. Have a look and
see what you think.

---

## How it works

The game is set in 2050. A player picks one large-scale intervention in one of seven
world regions, and Red Worlds answers: *how much carbon does that avoid, over the fifty
years to 2100, compared with not doing it?*

That last clause matters more than anything else here. Every number is a **difference
against a baseline**, never a forecast of the world in 2050.

### The method, in one idea

Every purchase drags a chain of production behind it. A solar panel needs steel; steel
needs coal; coal needs machinery; machinery needs steel again. **Input–output analysis**
is the standard way of solving that loop — a table of who buys what from whom across a
whole economy, arranged so you can ask what a change in demand does to total output, and
then to total emissions.

Our table is [EXIOBASE](https://www.exiobase.eu/): 200 product categories across 49
countries and regions, with CO₂ and other greenhouse gases attached. Built by a European
research consortium, its method set out in a
[peer-reviewed paper](https://doi.org/10.1111/jiec.12715). A serious, widely used
dataset — and a model of an economy in **2011**, with everything that implies.

### The three wings

Every intervention is one of three kinds. They differ in **what happens to the money**,
and that turns out to decide the answer.

**BUILD — construct new low-carbon capacity**, say a ten-reactor nuclear block. The money
is *moved* into investment: concrete, steel, machinery, electrical equipment, all emitting
now, years before the thing generates anything. So emissions rise before they fall — the
J-curve. That hump against the eventual fall is the whole argument about building your
way out.

**SWAP — substitute one product for another** at the same volume, motor fuel for
electricity in cars. The money is *kept*: a household spending less on petrol spends it
elsewhere, and that has a footprint too. The re-spend is the **rebound**, and we model it
deliberately — leaving it out is the commonest way to flatter a swap.

**REDUCE — consume less of a basket of products.** The money *leaves the model*, the
economy shrinks in proportion, and there is no rebound at all. A post-growth framing, and
a real choice rather than a neutral default — see below.

### Scoring

The annual difference against the baseline, spread across the fifty years through a
deployment curve — things arrive gradually, not all at once — then summed. The game sizes
every intervention to the same expected abatement; Red Worlds answers how much of each
one that takes, in each region.

---

## What we assume, and where it breaks

Every model makes choices. Here are ours, and the places they pinch.

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
assumption doing the heavy lifting. So the engine is open. Follow the assumptions rather
than the conclusions — it is the more interesting route anyway.

---

## Want to learn more? Drop a link to your AI and talk it through

We built this place with that in mind. The documents are in plain language, the
assumptions are stated rather than buried, and the whole thing is small enough for an
assistant to read in one sitting. Point one at it and you can:

- ask what any of this means, in whatever words make sense to you
- have it walk you through a modelling decision, one step at a time
- hold our assumptions up against what you already know
- get a coding assistant to clone the repo and run the engine alongside you

Simply copy this address:

```
https://github.com/nathmoore/redworlds
```

paste it into Claude, ChatGPT, Gemini, Copilot or whatever you already use, and say
*"read this repository and help me understand it"*. Then ask away — *"is the science here
real, or made up for a game?"*, *"why does a BUILD intervention make emissions rise before
they fall?"*, *"take me through how I'd model halving a region's cement use."*

One thing worth knowing: an assistant can explain the method, but it can't give you a
number. Those come from running the engine, which needs a 1.9 GB download and a few
minutes of computation. A confident figure in tonnes that arrived without a run was
invented.

[**docs/ai-guide.md**](docs/ai-guide.md) has more — a glossary, a way of taking a
modelling decision apart step by step, how to get an assistant to run EXIOBASE with you,
and the handful of mistakes they reliably make here.

---

## Prefer learning things old school? Here's some further reading we recommend 🤓

Ours, roughly in the order they are worth reading:

| | |
|---|---|
| Why the model does what it does, and its limits | [assumptions.md](docs/design/assumptions.md) |
| BUILD, SWAP and REDUCE in technical detail | [game_mechanics.md](docs/design/game_mechanics.md) |
| How the pieces fit together | [architecture.md](docs/design/architecture.md) |
| What the game requires of the engine | [red_carbon_contract.md](docs/design/red_carbon_contract.md) |
| What is built, in progress, or undecided | [backlog.md](docs/backlog.md) |
| Worked examples you can run yourself | [examples/](examples/) |
| Where the data comes from and how to get it | [data/README.md](data/README.md) |

And further afield:

- **[pymrio's documentation](https://pymrio.readthedocs.io/)** — the library doing the
  table maths, with the friendliest introduction to input–output analysis we know of.
- **[Sustainable Energy — Without the Hot Air](https://www.withouthotair.com/)**, David
  MacKay — free online, and still the clearest book written on sizing climate
  interventions honestly. If you read one thing on this list, read this.
- **[Stadler et al. 2018](https://doi.org/10.1111/jiec.12715)** — the peer-reviewed paper
  on how EXIOBASE is built, for when you want it from the source.
- **[EXIOBASE itself](https://www.exiobase.eu/)**, and
  [the exact release we use](https://doi.org/10.5281/zenodo.5589597).
- [docs/references.md](docs/references.md) — the full bibliography behind the engine.

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
