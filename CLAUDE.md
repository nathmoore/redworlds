# CLAUDE.md — Red Worlds

This file gives an AI coding assistant (or a human contributor) the context needed
to work on this repo effectively. Read this before writing or modifying any code.

---

## What this project is

**Red Worlds** is the open-source Python simulation engine for **Red Carbon**, a web game
about decarbonisation. It is NOT the game itself — the game's WordPress front end
lives in a separate private repo.

Red Worlds handles:
- **Player actions**: BUILD, SWAP, REDUCE — applied to a player's EXIOBASE IO tables
- **Overnight jobs**: advance the IO world by one simulation year; generate new scenarios
- **IO table maths**: pure functions on pymrio.IOSystem objects

The WordPress front end sends action results to this server; this server stores and
updates the player's IO world, then returns updated emissions figures.

---

## Repo structure

```
redworlds/
├── src/redworlds/
│   ├── actions/         ← player-triggered: build.py, swap.py, reduce.py
│   ├── jobs/            ← overnight batch: apply_growth.py, update_scenarios.py
│   ├── engine/          ← pure functions: io_tables.py, balancing.py
│   └── config.py        ← loads config/config.toml
├── tests/               ← mirrors src/redworlds/ structure
├── examples/            ← Jupyter notebooks for community users
├── data/
│   ├── concordances/    ← COMMITTED: sector and region mapping CSVs
│   ├── tech_choices/    ← COMMITTED: BUILD/SWAP/REDUCE options
│   ├── exiobase/        ← GITIGNORED: raw EXIOBASE downloads
│   └── worlds/          ← GITIGNORED: per-player IO tables
├── config/
│   ├── config.example.toml   ← COMMITTED: template
│   └── config.toml           ← GITIGNORED: personal paths
└── docs/
    ├── design/          ← architecture.md, assumptions.md, game_mechanics.md
    └── ...
```

---

## Three action types

| Action | What it does | Rebalances? | Matrix changed |
|--------|-------------|-------------|----------------|
| **BUILD** | CapEx over build period; energy mix shifts after | Yes | Z (construction), then A |
| **SWAP** | Shifts % of one sector's flows to a replacement | Yes | Y or Z depending on type |
| **REDUCE** | Reduces final demand — economy shrinks (post-growth) | No | Y |

See `docs/design/assumptions.md` for rationale on all three.

---

## Code standards

- **Python 3.12+** with type hints on all function signatures
- **Formatter/linter**: ruff (line length 120). Run `just qa` to check.
- **Type checker**: ty. Run `just type-check`.
- **Tests**: pytest. Every new function gets a corresponding test.
- **Package manager**: uv (`uv sync`, `uv add <package>`)
- **Task runner**: just (`just qa`, `just test`, `just docs-serve`)

---

## Game design principles

The engine exists to serve the game. Scientific accuracy matters, but fun and fairness
come first. Reference: **The Art of Game Design** by Jesse Schell (the project's
game design bible).

- BUILD, SWAP, and REDUCE must all feel viable. Game balance is the game designer's
  responsibility (with input from the community) — don't adjust model behaviour for balance reasons unless explicitly asked.
- Any simplification that makes the game more legible without being misleading is
  usually right. Document it in `docs/design/assumptions.md`.

See `docs/design/assumptions.md` for the full game design rationale.

---

## Code design principles

1. **Pure functions in `engine/`** — no side effects. Pass in an IOSystem, get one back.
2. **Classes only when state + behaviour coexist** — e.g. a Scenario or Portfolio object.
   Avoid classes for simple data containers; use dataclasses or TypedDicts.
3. **Small, single-responsibility functions** — if a function needs a long docstring
   to explain what it does, it probably does too much.
4. **Readable over clever** — this codebase is read by economists and students,
   not just software engineers. Prefer explicit variable names and simple logic.
5. **Follow pymrio conventions** — for any operation that pymrio supports natively
   (emissions extraction, matrix access, recalculation), use the pymrio API rather than
   reimplementing it. The pymrio docs are authoritative; check them before writing
   custom matrix operations.
6. **Leave TODOs with issue refs** — `# TODO: implement — see GitHub issue #N`.
   Don't leave TODOs without a corresponding GitHub issue.

---

## Testing approach

- **Default tests use `pymrio.load_test()`** — pymrio's built-in small IO world.
  These are fast, require no external data, and run in CI.
- **Integration tests use real EXIOBASE data** — marked `@pytest.mark.integration`,
  skipped by default. Run with `just test -m integration` after configuring `config/config.toml`.
- Tests mirror the `src/redworlds/` structure under `tests/`.
- The shared `test_mrio` fixture lives in `tests/conftest.py`.

---

## Writing style

Audiences: players, data enthusiasts, contributors, WordPress developers. Write for
the non-specialist first. Explain *why*, not just *what*. Plain language before
jargon. Confident about design decisions — frame open questions as invitations, not
hedges. Reference tone: `docs/design/assumptions.md`.

---

## Security

Player privacy is paramount. Never commit to this repo:
- Player data (emails, usernames, scores, play history)
- Production server URLs, hostnames, credentials, or API keys
- Anything that belongs in a private `.env` — use `config/config.toml` (gitignored)

When the API endpoint is built: authenticate every request, confirm `player_id`
matches the session, and validate all inputs at the boundary (not inside engine
functions). Actions in `actions/` can assume valid, authenticated input.

---

## What NOT to do

- Do not commit `data/exiobase/`, `data/worlds/`, or `config/config.toml` — these are gitignored.
- Do not add side effects to `engine/` functions.
- Do not over-abstract. Three similar lines of code is better than a premature abstraction.
- Do not add error handling for scenarios that can't happen in normal use.
- Do not add features not asked for. Leave a TODO + GitHub issue instead.
- Do not use `mrio` objects in `engine/` functions that also read from disk or config —
  keep IO operations in `jobs/` and `config.py`.

---

## Key data files (committed reference data)

| File | Purpose |
|------|---------|
| `data/concordances/exiobase_to_scenario.csv` | Maps EXIOBASE sectors to game scenario categories |
| `data/concordances/region_mapping.csv` | Maps EXIOBASE regions to the 6 amalgamated game regions |
| `data/tech_choices/options.toml` | BUILD/SWAP/REDUCE tech options with compatible scenario tags |
| `config/config.example.toml` | Template for personal `config/config.toml` |

---

## Common tasks

```bash
just qa              # ruff format + lint, ty type-check, pytest — run before every commit
just test            # pytest only
just test -m integration   # include integration tests (requires config/config.toml)
just docs-serve      # live docs at http://localhost:8000
just docs-build      # build docs in strict mode
just version         # print current version
```

---

## Backlog approach

Stubs use `raise NotImplementedError`. Always pair a stub with:
- `# TODO: implement — see GitHub issue #N` (real issue number required)
- A skipped test stub in the corresponding test file
