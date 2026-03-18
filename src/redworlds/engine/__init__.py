"""Core IO table operations and economic balancing logic.

These are pure functions (no side effects) that operate on pymrio.IOSystem objects.
They are called by the action modules (actions/) and job modules (jobs/).

- io_tables: Low-level operations on IO system arrays (sector scaling, mixing, extraction).
- balancing: Economic rebalancing to maintain a closed economy after a change.

Design principle: functions in this package should be small, single-responsibility,
and have no side effects. Pass in an IOSystem, get a new IOSystem back.
See docs/design/assumptions.md for the economic model assumptions baked in here.
"""
