# AGENTS.md — Red Worlds

The working agreement for this repository. It is written for whoever is doing the work:
a human contributor, or an AI coding agent (Claude Code, Codex, Cursor, Copilot, Gemini,
or whatever comes next). Read it before writing or modifying anything.

There is no second source of truth. `CLAUDE.md` points here.

---

## What this project is

**Red Worlds** is the open-source Python engine behind **Red Carbon**, a web game about
decarbonisation. It is not the game. The game's front end lives in a separate private repo.

Red Worlds handles:

- **The baseline** — a one-off job builds a 2050 world from the 2011 EXIOBASE table
  (SSP2 pathway, capital endogenised) and caches it.
- **Player actions** — BUILD, SWAP, REDUCE: one tape's shock applied to that baseline.
- **Scoring** — annual delta against the baseline → deployment curve → cumulative CO₂
  over 2050–2100.
- **IO table maths** — pure functions on `pymrio.IOSystem` objects.

The game plays one tape at a time, and asks the engine one question: how much CO₂ does
this intervention abate, over fifty years, in this region. Because every player-facing
shock is linear in the outcome fraction, each tape is solved **once, offline**, and ships
to the game as a small JSON table. A live server with a job queue is future state — it is
designed in `docs/design/architecture.md` but nothing here builds toward it yet, and you
should not add plumbing that assumes it.

Decisions the game has made that bind this engine — the time window, the scoring metric,
the brick normalisation, per-wing rebound rules, the calling contract, the shape of the
precomputed table — live in **`docs/design/red_carbon_contract.md`**. Where it disagrees
with any other document in this repo, it wins. `docs/backlog.md` holds sequencing and the
open modelling questions; GitHub issues hold implementable units.

---

## Three ways to work here

Most arrivals are doing one of three things. Each has a different entry point.

**1. Answering questions about the model** — someone wants to understand what this
computes and whether to believe it. Start at `docs/design/assumptions.md` (the rationale
for every design choice, including the known limitations) and `docs/references.md` (full
citations). Do not answer from the README alone; it is deliberately a summary. If the
question is about what the game requires rather than what the model does, the contract is
the authority.

**2. Changing code** — read this file, then the module you are touching, then its test.
Tests run without any EXIOBASE download, so you can verify almost everything in seconds.
Keep to the code design principles below; they are what make this readable to the
economists and students who are a real part of the audience.

**3. Running the engine** — see *How to run it*. The one thing to know before you start:
the full EXIOBASE download is ~1.9 GB and building the baseline takes minutes, not
seconds. Check whether a cached world already exists before rebuilding one.

---

## Repo structure

```
redworlds/
├── src/redworlds/
│   ├── actions/         ← one tape's shock: build.py, swap.py, reduce.py
│   ├── jobs/            ← reads data, calls engine: build_baseline.py, apply_growth.py, update_scenarios.py
│   ├── engine/          ← pure functions: io_tables.py, balancing.py, capital.py, scoring.py, currency.py, prices.py, regions.py
│   ├── cli.py           ← thin typer entry point
│   └── config.py        ← loads config/config.toml
├── tests/               ← mirrors src/redworlds/; tests/fixtures/ holds test-world concordances
├── examples/            ← Jupyter notebooks for community users
├── data/
│   ├── concordances/    ← COMMITTED: sector and region mapping CSVs
│   ├── tech_choices/    ← COMMITTED: BUILD/SWAP/REDUCE options
│   ├── exiobase/        ← GITIGNORED: raw EXIOBASE and capital-matrix downloads (~1.9 GB)
│   ├── worlds/          ← GITIGNORED: cached baseline worlds as parquet (~117 MB each)
│   └── exports/         ← GITIGNORED: the tape table shipped to the game
├── config/
│   ├── config.example.toml   ← COMMITTED: template
│   └── config.toml           ← GITIGNORED: personal paths
└── docs/
    ├── backlog.md       ← sequencing + open modelling decisions
    ├── references.md    ← full citations
    ├── ai-guide.md      ← working on this repo with an AI assistant
    └── design/          ← red_carbon_contract.md, assumptions.md, architecture.md, game_mechanics.md
```

---

## How to run it

```bash
uv sync                    # install (uv is the package manager — not pip, not poetry)
just qa                    # format, lint, type-check, test — run before every commit
just test                  # tests only
just test -m integration   # add the tests that need real EXIOBASE data
just type-check            # ty, on its own
just baseline              # build and cache the baseline world
just docs-serve            # live docs at http://localhost:8000
just docs-build            # strict build; fails on broken links
```

**Tests need no data.** The default suite runs against `pymrio.load_test()`, pymrio's
built-in miniature IO world. That is deliberate: anyone can clone this repo and have a
green test run in under a minute.

**Everything else needs the download.** `just baseline`, the integration tests and the
notebooks all read real EXIOBASE. Get the two files as described in `data/README.md`
(EXIOBASE 3.8.2 `IOT_2011_pxp` from Zenodo record 5589597; the Wood & Södersten capital
use matrix from record 7073276), then copy `config/config.example.toml` to
`config/config.toml` and point it at them.

**Orders of magnitude, so you know what you are starting.** Parsing and inverting the
7-region aggregated table takes a few minutes and produces a cached world that reloads in
seconds; each subsequent demand-side shock is then seconds, not minutes. A full-resolution
9800 × 9800 solve is closer to twenty minutes and several GB of memory — do not reach for
one casually, and never inside a test.

---

## Three action types

| Action | What it does | Money | Matrix changed |
|--------|-------------|-------|----------------|
| **BUILD** | Capex injected during the build years; electricity mix shifts after completion | Moved — reallocated into investment | Y (GFCF), then A and S |
| **SWAP** | Shifts a share of one product's demand to a replacement | Kept — the re-spend is a deliberate rebound | Y (later Z) |
| **REDUCE** | Cuts demand for a basket; the economy shrinks in proportion | Removed — it leaves the model, no rebound | Y |

**BUILD moves money, SWAP keeps it, REDUCE removes it.** That one line is the whole
economic design. Capital is endogenised in the baseline (Södersten et al. 2018), so
consumer-demand tapes carry their capital consequences automatically.

Rationale for all three: `docs/design/assumptions.md`.

---

## Code standards

- **Python 3.12+** with type hints on every function signature.
- **Formatter and linter**: ruff, line length 120.
- **Type checker**: ty.
- **Tests**: pytest. Every new function gets a test.
- **Package manager**: uv (`uv sync`, `uv add <package>`).
- **Task runner**: just.

## Code design principles

1. **Pure functions in `engine/`** — no side effects. Pass in an IOSystem, get one back.
   Reading files and config belongs in `jobs/` and `config.py`.
2. **Classes only when state and behaviour genuinely coexist** — a Scenario or Portfolio
   object, say. For plain data, use a dataclass or a TypedDict.
3. **Small, single-responsibility functions** — if a function needs a long docstring to
   explain what it does, it probably does too much.
4. **Readable over clever** — this codebase is read by economists and students, not only
   by software engineers. Explicit names, simple logic, no point-free tricks.
5. **Follow pymrio conventions** — for anything pymrio supports natively (emissions
   extraction, matrix access, recalculation), use its API rather than reimplementing it.
   The pymrio docs are authoritative; check them before writing custom matrix operations.
6. **Leave TODOs with issue refs** — `# TODO: implement — see GitHub issue #N`. No
   orphan TODOs.
7. **EXIOBASE is the primary IO database, but not the only conceivable one** — engine
   functions target EXIOBASE 3.8.2 (pxp). Where code is genuinely EXIOBASE-specific
   (currency constants, region concordance, price markup), mark it `# EXIOBASE-specific`
   so a contributor extending to WIOD, Eora or GLORIA knows what to replace.

## Testing approach

- Default tests use `pymrio.load_test()` — fast, no external data, run in CI.
- Integration tests are marked `@pytest.mark.integration` and skipped by default. Run
  them with `just test -m integration` once `config/config.toml` exists.
- Tests mirror the `src/redworlds/` structure.
- Shared fixtures live in `tests/conftest.py`.

---

## Modelling discipline

This repo makes claims about the world, so a modelling change is not the same kind of
change as a refactor. Four rules:

1. **Do not tune the model to make the game work.** BUILD, SWAP and REDUCE must all be
   viable choices in the game, but that is the game designer's problem, solved on the
   game side. Never adjust model behaviour for balance reasons unless explicitly asked.
   An engine that flatters one wing is worth nothing to anybody.
2. **Simplify freely; document every simplification.** A simplification that makes the
   result more legible without making it misleading is usually right. It goes in
   `docs/design/assumptions.md` the moment it is made, not later.
3. **Cite inline, in short form.** Where a number or an assumption comes from a source,
   name it where it lives in the code or the commit body (`ECB 2011 annual average
   EUR/USD = 1.3917`). Full citations belong in `docs/references.md`.
4. **Open questions are open in writing.** `docs/backlog.md` holds the modelling
   decisions that still need thinking or a model run. When one is settled it graduates
   into `docs/design/assumptions.md`. There is no separate decisions log here — commit
   bodies carry the reasoning trail.

Stubs use `raise NotImplementedError`, and always come in threes: the stub, a
`# TODO: implement — see GitHub issue #N` (or a pointer to `docs/backlog.md` until the
issue exists), and a skipped test in the mirroring test file.

---

## This repo is public

Red Worlds is public, CC BY-SA 4.0, and on PyPI. Its git history is permanent: anything
committed here is out for good, including from a branch that is later deleted.

**Never commit:**

- Anything from the game's private repo — story, characters, dialogue, beat sheets,
  the reasons a particular intervention is in the game. The engine's half of the work is
  the mechanism; the game's half is the argument, and it does not cross.
- Player or playtester data of any kind: names, emails, scores, play history, session
  logs.
- Production hostnames, URLs, credentials, API keys.
- `config/config.toml`, `data/exiobase/`, `data/worlds/`, `data/exports/` — all
  gitignored, all either private paths or large licensed data.

**Fine to state in full:** the time window, the scoring metric, the brick normalisation,
the per-wing rebound rules, the calling contract, tape ids with their wings and
mechanisms, research numbers with public sources, and any open modelling question.

The test, when you are unsure: **could a contributor with only this repo understand and
act on what you are about to write?** If it needs the private repo to make sense, it
does not belong here.

When the API is eventually built: authenticate every request, validate at the boundary
rather than inside engine functions, and let `actions/` assume its input is already
valid and authenticated.

---

## Working alongside others

This repo is worked on by a human and by more than one AI tool, sometimes in the same
week. Assume you are arriving mid-thought.

Before editing:

1. Check `git status` and read the relevant diffs. Uncommitted work is normal here.
2. Assume unfinished-looking code is intentional scaffolding until you have checked.
   Search for references to it; look at the backlog; look at the test file beside it.
3. Prefer completing or extending existing scaffolding over replacing it.
4. Look for a nearby pattern before introducing a new one.
5. Keep changes small, local and reviewable.
6. Stage specific paths. Never `git add -A` — other work may be in flight.

Pause and ask before proceeding if the rationale for existing scaffolding is unclear, if
several implementation directions look equally plausible, if the task seems to need an
architectural change, or if it would embed a scientific assumption that is not already
written down. When you ask, first say what you think the existing structure does, what
you would assume, which files you expect to touch, and what you are unsure of.

For small, obvious, reversible edits, just make the minimal diff.

---

## Git commits

Conventional commits: `type(scope): short imperative summary (≤72 chars)`

Types: `feat` · `fix` · `docs` · `refactor` · `test` · `data` · `chore`

**Body rules:**

1. A body is required whenever a decision could be misread or a scientific assumption is
   embedded. Explain *why*; the diff already shows what.
2. Omit the body for genuinely mechanical changes — typos, formatting, version bumps.
3. Cite sources inline in short form where an assumption rests on one.
4. If the commit updates `docs/design/assumptions.md`, the body can state the conclusion
   briefly and point at the doc for the argument.
5. If an AI tool wrote the majority of the change, credit it on the last line:
   `Co-Authored-By: <model or tool name> <noreply@example.com>`. Use the address the tool
   itself specifies. One line; the point is an honest record of authorship, not a badge.

**Template:**

```
type(scope): short summary

Why this change was made — one paragraph. Explain the decision or the assumption,
not the mechanics. A future contributor should understand the reasoning without
opening the code.

Source: short-form citation if applicable.

Co-Authored-By: ...
```

---

## What not to do

- Do not commit gitignored data or config.
- Do not add side effects to `engine/` functions.
- Do not over-abstract. Three similar lines beat a premature abstraction.
- Do not add error handling for situations that cannot occur in normal use.
- Do not add features nobody asked for. Leave a TODO and an issue instead.
- Do not build toward the live server, the job queue or per-player worlds. They are
  designed, not scheduled.
- Do not present a stub as though it were implemented — in code, in docs, or in an
  answer to a user.

---

## After making changes

Summarise, concisely and tied to the actual diff:

- files changed
- what was implemented
- what you assumed
- what checks you ran (and their result)
- what you did **not** verify
- any risk or follow-up worth knowing about

If you could not run the tests, say so plainly rather than implying they passed.
