# Architecture

Red Worlds is a Python simulation server. This document describes the system as a whole,
the data flow, and what lives where.

---

## System overview

```
Red Carbon (WordPress)              Job Queue DB          Red Worlds (this repo)
──────────────────────              ────────────          ──────────────────────
Player completes turn   ──insert──► job row               worker polls for jobs
                                    (status=pending)  ◄── claims job
                                                          │
                                                          │ actions/ → engine/
                                                          │ reads/writes IO tables
                                                          │
                        ◄─update─── result_json       ──► writes result + progress
                        polls for   (status=done)
                        status

─────────────────────────────────────────────────────────────────────────────────
Overnight (server cron)
────────────────────────
jobs/apply_growth.py      ─── advances each player's world by 1 simulation year
jobs/update_scenarios.py  ─── generates the next day's scenario
```

---

## Data flow: player action

1. Player completes a Decarbonator Deck session on Red Carbon.
2. WordPress inserts a job record into the shared queue database:
   - `action`: `build`, `swap`, or `reduce`
   - `player_id`, `payload_json` (region, technology, numeric Deck outputs), `status: pending`
3. The Red Worlds worker claims the job (sets `status: processing`).
4. The action module loads the player's IO system, calls engine functions, saves the result.
5. Intermediate calculation steps are written to `progress_json` as they complete —
   Red Carbon polls this to drive the "calculating" animation.
6. Final result is written to `result_json`: updated emissions, key stats, any animation numbers.
   Job status set to `done`.
7. Red Carbon reads the result and updates the player's display.

**On JSON vs separate files:** the action payload and result are small enough to live in the
queue DB record — no need for separate files per turn. The IO tables themselves are stored
separately (see below).

---

## Data flow: overnight jobs

1. Nightly cron calls `jobs/apply_growth.py` for each player's world.
2. Growth is applied and the IO table is overwritten (no duplication — old state is not kept).
3. Baseline emissions are recalculated and written to the player's daily stats record.
4. `jobs/update_scenarios.py` generates the next scenario using the concordance tables.

---

## Data retained per player

The goal is to keep what's needed for in-game stats, game designer review, and debugging —
without storing redundant or recoverable data.

| Data | Storage | Retained how long |
|------|---------|------------------|
| Current IO tables | `data/worlds/<player_id>/` file | Overwritten each action and each overnight run |
| Daily stats snapshot | Lightweight DB record or JSON: emissions, score, year | Kept indefinitely — basis for in-game graphs |
| Per-action log | DB record or JSON: action type, params, emissions before/after | Kept — audit trail for game designer review |
| Job queue records | DB rows | Keep for N days, then archive or prune |
| Year baseline snapshot | Emissions vector only (not full IO table) | Kept — for year-over-year comparison |

Full IO table history is not retained — tables are large and can be reconstructed by
replaying the action log from the baseline EXIOBASE. The action log is the ground truth.

---

## Logging

Standard Python `logging` with structured output to file and stderr. Log levels:

- `DEBUG`: IO table operation details (useful during early testing)
- `INFO`: job start/complete, overnight job progress
- `WARNING`: unexpected values, slow jobs
- `ERROR`: job failures — written to the job record and to the log

In early testing, run at `DEBUG` level. Production will use `INFO`.
Log file location is configured in `config/config.toml`.

---

## pymrio recalculation notes

The three actions operate on different parts of the IO system, which determines
how much recalculation is required after each change:

| Action | Matrix changed | Recalculation needed |
|--------|---------------|---------------------|
| REDUCE | Y (final demand) | x = L·y, then S, M, D — relatively fast |
| SWAP (consumer-side) | Y | Same as REDUCE |
| SWAP (production-side) | Z (intermediate) | A = Z·x̂⁻¹, L = (I−A)⁻¹, then full chain — expensive |
| BUILD (during build period) | Z (construction sectors) | Full recalculation |
| BUILD (post-build) | A (energy mix change) | Full recalculation |

In practice: REDUCE and Y-side SWAP are cheap; anything touching Z or A requires
the full Leontief recalculation. The `engine/io_tables.py` functions should accept
a flag or return a hint indicating which recalculation is needed, rather than always
calling `calc_all()` on every change.

*The exact matrix targets for each action type are to be confirmed against the pymrio
docs and EXIOBASE structure during implementation — treat the above as a working hypothesis.
See also `docs/design/assumptions.md`.*

---

## Module responsibilities

| Module | Responsibility | Side effects? |
|--------|---------------|---------------|
| `actions/build.py` | Orchestrate a BUILD action | Reads/writes player world |
| `actions/swap.py` | Orchestrate a SWAP action | Reads/writes player world |
| `actions/reduce.py` | Orchestrate a REDUCE action | Reads/writes player world |
| `jobs/apply_growth.py` | Advance world by one simulation year | Reads/writes player world |
| `jobs/update_scenarios.py` | Generate a new daily scenario | Reads concordances, writes scenario |
| `engine/io_tables.py` | Low-level IO array operations | None — pure functions |
| `engine/balancing.py` | Economic rebalancing | None — pure functions |
| `config.py` | Load config/config.toml | Reads config file |

---

## What lives where

| Data | Location | Committed? |
|------|----------|-----------|
| Player IO tables | `data/worlds/` | No — gitignored |
| Raw EXIOBASE files | `data/exiobase/` | No — gitignored (licensed, large) |
| Sector-to-scenario mapping | `data/concordances/exiobase_to_scenario.csv` | Yes |
| Region mapping | `data/concordances/region_mapping.csv` | Yes |
| Tech choices (BUILD/SWAP/REDUCE options) | `data/tech_choices/options.toml` | Yes |
| Personal config (data paths, log paths) | `config/config.toml` | No — gitignored |
| Config template | `config/config.example.toml` | Yes |
| Job queue + player stats | Database (TBC — not yet implemented) | No |

---

## Technology choices

| Concern | Tool | Why |
|---------|------|-----|
| IO table engine | [pymrio](https://pymrio.readthedocs.io) | Standard Python MRIO library; used by EXIOBASE researchers |
| Data format | EXIOBASE 3 ixi (pymrio format) | CC BY-SA 4.0, industry-standard |
| Job queue | TBC (DB table or lightweight queue) | To be chosen — simple DB table likely sufficient for MVP |
| Config | TOML | Human-readable, easy to diff |
| Package manager | uv | Fast, deterministic |
| Task runner | just | Simple Makefile alternative |
