# History

## Unreleased

Work since 0.1.0, not yet published to PyPI.

**The baseline walk begins (November 2026).** The first step of walking the 2011 table
forward on explicit, sourced assumptions: an electricity step that moves a region's
generation mix while conserving kilowatt-hours, a data-preparation job for Ember's open
electricity data, and a hindcast from 2011 to 2025 that follows the observed fall in the
carbon intensity of generation. Design in `docs/design/baseline_walk.md`; build order and
results in `docs/plans/03-baseline-walk.md`.

**Nine tapes with real numbers (September 2026).** The engine went from scaffolding to a
table the game can score from:

* Final-demand scaling, consumption-based emissions and the REDUCE action.
* Capital endogenised in the baseline from the published capital use matrices, and the
  aggregated seven-region baseline cached for reuse.
* The SWAP action with a closed household budget; BUILD in two phases, construction capex
  and an operating-phase change to the electricity recipe; a grid-efficiency tape.
* Scoring: annual delta, deployment curves, cumulative delta over 2050–2100, GDP impact.
* Weighted baskets, a non-linear product-lifetime cover, and household road emissions
  derived from fuel factors.
* The export job: one deterministic JSON table of all nine tapes, with CO₂ and CO₂e, each
  tape's value at its cover, and its calibration stated as a field.
* The 2011 to 2050 intensity correction split into an observed stage and a scenario stage.
* Documentation rebuilt around the game's 2050 contract: `AGENTS.md` as the working
  agreement, a guide for exploring the repo with an AI assistant, numbered plans that close.

## 0.1.0 (2026-03-15)

* First release on PyPI.
