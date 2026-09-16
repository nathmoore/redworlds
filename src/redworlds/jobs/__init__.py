"""Jobs: the code that reads data and config and calls the pure engine.

- build_baseline: one-off, on the MVP path — 2011 EXIOBASE → capital endogenised →
  SSP2 2050 world → 2050–2100 trajectory, cached.
- apply_growth: step a world forward one year (used by build_baseline; nightly in phase 2).
- update_scenarios: phase 2 — generate a daily scenario from a target category.
"""
