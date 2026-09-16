# Architecture

Red Worlds is a Python simulation engine with a thin server around it. This document
describes the system as a whole, what is on the MVP path, and what lives where.

---

## Two phases

**MVP: a stateless scoring function.** One cached baseline world for 2050, one tape's
shock, one Leontief solve, a deployment curve, a fifty-year cumulative delta. A notebook
can call it directly; the server is a loop that reads jobs and calls the same function.

**Phase 2: per-player worlds and interaction.** Each player's world persists across a
week, tapes played on the same day interact non-additively (a feature the game wants), and
a nightly job advances worlds. The queue design below serves both phases; nothing in the
MVP has to be rewritten to get there.

---

## System overview

```
Red Carbon (WordPress, private)      Job queue (DB table)     Red Worlds (this repo)
──────────────────────────────       ────────────────────     ──────────────────────
finale-resolution module resolves    job row inserted    ──►  worker claims job
dice + civic + push → outcome        (status=pending)         │ reads tape record
fraction, emits payload_json                                  │ loads cached baseline
                                                              │ actions/ → engine/
                          ◄── polls  progress_json       ◄──  │ writes progress per step
                          ◄── reads  result_json         ◄──  writes result, status=done
                                     (status=done)

One-off / occasional
────────────────────
jobs/build_baseline.py   2011 EXIOBASE → capital endogenised → SSP2 2050 world (+ 2050–2100 trajectory), cached
jobs/apply_growth.py     the year-stepping used inside build_baseline (phase 2: nightly per-player advance)
jobs/update_scenarios.py phase 2: generate the day's scenario / tape shelf
```

---

## Data flow: one tape

1. Player commits a tape; the game resolves the roll and inserts a job row:
   `player_id`, `tape_id`, `region_id`, `outcome_fraction`, `push_level`,
   `modifier_effects`, `status: pending`.
2. The worker claims the job (`status: processing`).
3. It reads the tape record from `data/tech_choices/options.toml`, derives the engine
   inputs, loads the cached baseline, and calls the action function.
4. `engine/scoring.py` turns the shocked world into an annual delta against baseline,
   runs it through the deployment curve, and produces the cumulative and the curve.
5. Each step appends to `progress_json`; the game polls it to drive the "calculating"
   animation.
6. `result_json` is written and the job marked `done`. Shapes are in
   [`game_mechanics.md`](game_mechanics.md).

Payload and result are small enough to live in the queue row. The baseline world is a
file on disk, loaded once per worker process.

---

## Data retained

| Data | Storage | MVP | Retained |
|------|---------|-----|----------|
| Cached baseline world (2050, capital endogenised, L precomputed) | `data/worlds/baseline_2050/` | yes | Rebuilt when the baseline recipe changes |
| Baseline emissions trajectory 2050–2100 | alongside the baseline | yes | same |
| Job rows (payload, progress, result) | DB table | yes | Keep for N days, then prune |
| Per-tape result log | DB or JSON: tape, inputs, result | yes | Kept — audit trail for the game designer and for calibration |
| Per-player worlds | `data/worlds/<player_id>/` | phase 2 | Overwritten each action |

Full IO-table history is never kept; a world can be reconstructed by replaying the result
log against the baseline.

---

## Logging

Standard Python `logging` with structured output to file and stderr. `DEBUG` for IO
operation detail during early testing, `INFO` for job start/complete, `WARNING` for
unexpected values or slow solves, `ERROR` for job failures (also written to the job row).
Log file location is configured in `config/config.toml`.

---

## pymrio recalculation notes

| Change | Matrix | Recalculation |
|--------|--------|---------------|
| REDUCE | Y | `x = L·y`, then S, M, D — cheap, cached L reused |
| SWAP (consumer side) | Y | same |
| BUILD, construction phase | Y (GFCF column) | same |
| BUILD, post-build energy mix | A and S | full: A, L = (I − A)⁻¹, downstream chain — expensive |
| SWAP (production side) | Z / A | full |
| Capital endogenisation | A (baseline only) | full, once |

Y-side changes are the MVP path. Functions in `engine/io_tables.py` should tell the caller
which recalculation is needed rather than always calling `calc_all()`.

---

## Module responsibilities

| Module | Responsibility | Side effects? |
|--------|---------------|---------------|
| `actions/build.py` | Apply a BUILD shock (capex injection, then mix change) | None — pure |
| `actions/swap.py` | Apply a SWAP shock and rebalance | None — pure |
| `actions/reduce.py` | Apply a REDUCE shock, no rebalance | None — pure |
| `engine/io_tables.py` | Shock primitives on IO arrays | None — pure |
| `engine/balancing.py` | Rebalancing with a weighting argument | None — pure |
| `engine/capital.py` | Endogenise capital into A from the capital use matrix | None — pure |
| `engine/scoring.py` | Annual delta vs baseline → deployment curve → cumulative | None — pure |
| `engine/currency.py` | Convert 2011 MEUR → 2026 constant MUSD | None — pure |
| `engine/prices.py` | Basic ↔ purchaser prices | None — pure |
| `engine/regions.py` | Aggregate 49 EXIOBASE regions → 7 game regions | None — pure |
| `jobs/build_baseline.py` | Build and cache the 2050 baseline | Reads EXIOBASE and capital data, writes cache |
| `jobs/apply_growth.py` | Step a world forward one year | Reads growth data |
| `jobs/update_scenarios.py` | Phase 2: generate the day's scenario | Reads concordances |
| `config.py` | Load `config/config.toml` | Reads config file |

The rule: `engine/` never touches disk or config. Anything that does lives in `jobs/` or
the server loop.

---

## What lives where

| Data | Location | Committed? |
|------|----------|-----------|
| Raw EXIOBASE files | `data/exiobase/` | No — gitignored (large; CC BY-SA) |
| Capital use matrices | `data/exiobase/capital/` | No — gitignored (large; CC-BY-4.0) |
| Cached baseline and per-player worlds | `data/worlds/` | No — gitignored |
| Sector-to-scenario mapping | `data/concordances/exiobase_to_scenario.csv` | Yes |
| Region mapping | `data/concordances/region_mapping.csv` | Yes |
| Tape records | `data/tech_choices/options.toml` | Yes |
| Personal config | `config/config.toml` | No — gitignored |
| Config template | `config/config.example.toml` | Yes |
| Job queue and result log | Database (TBC) | No |

---

## Technology choices

| Concern | Tool | Why |
|---------|------|-----|
| IO engine | [pymrio](https://pymrio.readthedocs.io) | Standard Python MRIO library; used by EXIOBASE researchers |
| Data | EXIOBASE 3.8.2 pxp + capital use matrices | CC BY-SA 4.0 / CC-BY-4.0, product resolution |
| Job queue | DB table (TBC) | Simple polling is sufficient at this scale |
| Config | TOML | Human-readable, easy to diff |
| Package manager | uv | Fast, deterministic |
| Task runner | just | Simple Makefile alternative |
