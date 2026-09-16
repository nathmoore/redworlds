"""Player-triggered action calculations.

Each module corresponds to one of the three wings a Red Carbon tape can belong to:

- build: Construct new low-carbon capacity (e.g. wind farms, nuclear plants).
- swap: Replace a fraction of an existing technology with a cleaner alternative.
- reduce: Reduce consumption of a basket of products (no economic rebalancing).

The actions compose the shock primitives in engine/io_tables.py; the job handler derives
their inputs from the tape record and the game's outcome fraction
(docs/design/game_mechanics.md).
"""
