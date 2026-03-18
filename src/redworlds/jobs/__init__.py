"""Overnight batch jobs that prepare each player's world for a new simulation day.

Jobs run server-side on a schedule (e.g. nightly cron). They are not triggered
by player actions.

- apply_growth: Advance the IO tables by one simulation year (economic growth,
  population changes, etc.) and calculate the baseline emissions for that year.
- update_scenarios: Generate a new daily scenario from a target emissions category,
  using concordance tables to map to EXIOBASE sectors.
"""
