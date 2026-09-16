"""Core IO table operations and economic balancing logic.

These are pure functions (no side effects) that operate on pymrio.IOSystem objects.
They are called by the action modules (actions/) and job modules (jobs/).

- io_tables: Shock primitives on IO system arrays (scale, shift, extract emissions).
- balancing: Economic rebalancing with a weighting argument.
- capital: Endogenise capital into A (baseline construction only).
- scoring: Annual delta vs baseline → deployment curve → 50-year cumulative.
- currency, prices, regions: unit conversions and region aggregation.

Design principle: functions in this package should be small, single-responsibility,
and have no side effects. Pass in an IOSystem, get a new IOSystem back.
See docs/design/assumptions.md for the economic model assumptions baked in here.
"""
