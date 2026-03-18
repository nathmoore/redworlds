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

## Design principles

1. **Pure functions in `engine/`** — no side effects. Pass in an IOSystem, get one back.
2. **Classes only when state + behaviour coexist** — e.g. a Scenario or Portfolio object.
   Avoid classes for simple data containers; use dataclasses or TypedDicts.
3. **Small, single-responsibility functions** — if a function needs a long docstring
   to explain what it does, it probably does too much.
4. **Readable over clever** — this codebase is read by economists and students,
   not just software engineers. Prefer explicit variable names and simple logic.
5. **Leave TODOs with issue refs** — `# TODO: implement — see GitHub issue #N`.
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

## Writing style for docs and docstrings

Red Worlds has four distinct audiences (players, data enthusiasts, contributors,
integration developers) and the docs need to work for all of them. When writing
any documentation, docstring, or comment:

- **Be open and explanatory, not just terse.** A design document should read like a
  thoughtful professional explaining their reasoning — not like a changelog. Explain
  *why*, not just *what*.
- **Be direct and avoid padding.** Clear and warm is not the same as long. Don't add
  sentences that don't carry information.
- **Assume a smart but non-specialist reader.** The player or data enthusiast reading
  `assumptions.md` may not know what a Leontief inverse is. Use plain language first,
  technical terms second. A brief parenthetical is fine; a jargon wall is not.
- **Make design decisions feel considered, not apologetic.** When documenting a
  deliberate choice (e.g. REDUCE not rebalancing), explain the reasoning confidently.
  It's fine to note that it could be revisited — but frame it as an invitation, not a hedge.
- **One voice across the repo.** Docs, docstrings, and README should feel like they
  were written by the same thoughtful person. Avoid wildly different tones between files.

The reference tone is `docs/design/assumptions.md` — aim for that register.

---

## Security requirements

All action payloads arrive from the WordPress front end and must be treated as
untrusted input — even though the schema is documented publicly.

Before any action function does real work, the calling layer (API endpoint, not
implemented yet) must:

1. **Authenticate** — verify the request carries a valid signed token from WordPress.
2. **Authorise** — confirm the `player_id` in the payload matches the authenticated session.
   A player must not be able to modify another player's world.
3. **Validate inputs** — enforce bounds on all numeric fields:
   - `pct_rollout`, `pct_reduction`: must be in `[0.0, 1.0]`
   - `budget`, `build_years`: must be positive
   - `technology`, `sector`, `region`: must be present in the reference data (`options.toml`, `region_mapping.csv`)

The action functions in `actions/` themselves can assume valid, authenticated input.
Put validation at the API boundary, not scattered through engine logic.

Note: the JSON payload schemas in `docs/design/game_mechanics.md` are intentionally
public — they are discoverable from browser devtools anyway. Security comes from
server-side controls, not obscurity.

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

This is an early-stage project. Many functions are stubs (`raise NotImplementedError`).
The right way to handle unimplemented items:

1. Leave the function stub with a clear docstring and signature.
2. Add `# TODO: implement — see GitHub issue #N` with a real issue number.
3. Add a skipped test stub in the corresponding test file.

Do not attempt to implement everything at once. Prioritise clarity over completeness.

---

## Audiences (who reads this code)

1. **Red Carbon players** — curious about the science behind the game
2. **Data/scenario enthusiasts** — want to run their own IO scenarios with EXIOBASE
3. **Contributors** — want to improve logic or raise issues
4. **WordPress integration developers** — connecting the front end to this server

When writing docstrings and comments, aim for audience 1 and 2 to be able to
follow the logic, not just audience 3 and 4.
