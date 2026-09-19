# Explore this repo with an AI

The README shows the quick version: point an assistant at this repository and ask it
things. This page is for going further — using an AI to work *through* the model rather
than just read about it, and knowing where it will let you down.

Nothing here is specific to one assistant. It applies to Claude, ChatGPT, Gemini,
Copilot and anything else that can read a repository.

---

## What a read can answer, and what needs a run

The repository is written to be legible without being executed. An assistant that has
read it can explain the method, the assumptions and the reasoning, and can walk you
through what *would* happen to the tables under a given intervention.

It cannot give you a number. Numbers come out of the engine, and the engine needs a
1.9 GB EXIOBASE download and a few minutes of computation. If an assistant offers you a
confident figure for "how much CO₂ this would save" without having run anything, it has
generated the figure, not computed it.

| You want | You need |
|---|---|
| How the method works, what it assumes, what it ignores | A read |
| Which matrices an intervention touches, and in what order | A read |
| Whether a mechanism is expressible in EXIOBASE at all | A read, usually |
| Which EXIOBASE products correspond to a real-world thing | A read, then a check against the actual product list |
| Any quantity in tonnes, dollars or percent | A run |

---

## A short glossary, so the answers make sense

Red Worlds uses **input–output analysis**. The idea: every purchase pulls a chain of
upstream production behind it. Buying a solar panel requires steel, which requires coal,
which requires energy, which requires more steel. IO tables capture that whole recursive
supply chain in one matrix.

| Symbol | What it is |
|---|---|
| **Z** | Intermediate demand — what every sector buys from every other sector |
| **Y** | Final demand — households, government, investment |
| **A** | Technical coefficients: Z normalised by output. The "recipe" for each sector. With capital endogenised, the recipe also includes the capital goods a sector consumes per unit of output |
| **L** | The Leontief inverse, (I − A)⁻¹ — the full multiplier matrix, which is where the recursion gets solved |
| **F** | Satellite flows — emissions in physical units |
| **S** | Satellite intensity — emissions per unit of output |
| **D** | The footprint, S · L · Y — the number players ultimately care about |

A tape modifies **Y** (REDUCE, SWAP, and BUILD's construction phase) or **A** and **S**
(BUILD once the new capacity is operating). The engine recalculates downstream, takes the
annual difference against the baseline, runs it through a deployment curve and sums the
fifty years to 2100.

One thing worth holding on to: **results are meaningful relative to the baseline, not as
absolute levels.** The interesting question is always "compared to not doing it".

---

## Working a modelling decision with an assistant

This is the most useful thing an AI can do here, and it is not the same as asking it for
an answer. A modelling decision is a chain of choices, most of which have no single right
option, and the value is in being walked through the chain rather than handed the end of
it.

A decision worth working through usually looks like: *I want to know what would happen
if X.* The chain from there:

1. **Is X a thing that can happen to an economy's demand or its production recipes?**
   If neither, EXIOBASE cannot see it, and no amount of cleverness downstream recovers
   that. This is the question that kills bad ideas early and cheaply.
2. **Which of the three actions is it?** Does the money move (BUILD), stay (SWAP), or
   leave (REDUCE)? Get this wrong and the answer will be wrong by a large factor, in a
   direction that looks plausible.
3. **Which products, exactly?** EXIOBASE has ~200 product categories with specific
   labels. "Cars" is not one of them. This step ends in a list of real labels, checked
   against the product list, not guessed.
4. **Which region, and what is the ceiling?** Interventions are bounded by what is
   physically there. A region cannot electrify more vehicles than it has.
5. **What does this deliberately not capture?** Every answer has an honest footnote.
   `docs/design/assumptions.md` § Known limitations is the standing list; your decision
   probably adds one.

Ask the assistant to take you through those five in order and to stop at each one rather
than racing to a conclusion. Ask it to tell you which step it is least sure about. The
step it is least sure about is usually step 3.

The two documents that settle disputes: `docs/design/assumptions.md` for why the model
does what it does, and `docs/design/red_carbon_contract.md` for what the game requires of
it. If an assistant's answer contradicts either, the document wins.

---

## Running the engine with a coding agent

If you use an agentic coding tool — Claude Code, Codex, Cursor or similar — it can do
more than explain. Clone the repo and let it drive:

```bash
git clone https://github.com/nathmoore/redworlds.git
cd redworlds
uv sync
just test      # green in under a minute, no data needed
```

That first test run is the useful checkpoint: the default suite uses pymrio's built-in
miniature world, so a working clone proves itself before you download anything.

To go further you need the data. Ask the agent to walk you through `data/README.md`,
which has the two Zenodo downloads and the reasons for them, then to set up
`config/config.toml` from the example. Then:

```bash
just baseline                # build and cache the 2050 baseline world — minutes, not seconds
just test -m integration     # the tests that use real EXIOBASE
uv run jupyter lab           # the notebooks in examples/
```

`examples/03_first_reduce_number.ipynb` is the best place to see a real result being
produced end to end. Ask the agent to run it, then to change one thing in it and explain
what moved and why.

Two warnings for this lane. Building a baseline is not free — it reads gigabytes and
takes minutes, and an agent that decides to rebuild one unprompted has cost you a coffee
break. And a full-resolution 9800 × 9800 solve is roughly twenty minutes and several GB
of memory; the 7-region aggregation exists precisely so you do not have to do that.

---

## Using it for literature work

`docs/references.md` is a real bibliography, not a formality — EXIOBASE and its method
paper, the capital use matrices, pymrio, and the input–output scenario literature that
this engine's methods are drawn from (Wiebe, Vita, Cap, Bjelle, Södersten, Simas, Ivanova
and Wood, among others), plus the climate physics the game's temperature conversion rests
on.

It is a good spine for an assistant to work from: ask it which paper in that list is the
methodological precedent for a given technique, then go and read that paper. Asking it to
summarise papers it has not been given is a different and much less reliable activity.

---

## Where assistants reliably go wrong here

Five failure modes, in roughly descending order of how often they happen:

1. **Inventing EXIOBASE product labels.** The categories have precise names and an
   assistant will produce plausible ones that do not exist. The authority is the
   `products.txt` in the EXIOBASE download; the region equivalent is
   `data/concordances/region_mapping.csv`. Always check.
2. **Reporting a stub as though it worked.** Parts of this engine raise
   `NotImplementedError` by design, each paired with a skipped test. What is built
   changes week to week; `docs/backlog.md` is the current state, and any status list
   written anywhere else is probably out of date.
3. **Producing numbers from nowhere.** See above. A figure that did not come from a run
   came from the assistant's priors.
4. **Confusing the engine with the game.** This repo has no story, characters or
   scoring-for-players in it; the game's front end is a separate private repo. If an
   answer starts describing gameplay, it is confabulating.
5. **Treating a simplification as an error.** Constant trade shares, no price channel,
   seven aggregated regions, one baseline year — these are deliberate, documented and
   normal for demand-driven MRIO work. The honest framing is what the model is for and
   what it is not, and `docs/design/assumptions.md` § Known limitations says it plainly.

---

## If you want to contribute what you find

`AGENTS.md` at the repository root is the working agreement — how to run things, the code
and modelling standards, and what must never be committed to a public repo. It is written
for humans and AI assistants alike, and it is worth reading before an assistant opens a
pull request on your behalf.
