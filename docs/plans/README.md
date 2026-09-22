# Plans

Numbered implementation plans: scaffolding for a bounded piece of work, written so a session
can pick it up and act. **They are not a record of what is outstanding.**

| Plan | Status | Intent |
|---|---|---|
| [01 — Spike sprint](01-spike-sprint.md) | Closed 2026-09-22 | First numbers out of the real model, cheapest path first |
| [02 — Tape completion](02-tape-completion.md) | Closed 2026-09-22 | Nine tapes with real numbers and covers sized to the peg |

## How to read one

Check the **`Status:`** line first. A closed plan's unticked boxes are **history, not work** —
they record what the plan did not reach, not what anybody should do next. Do not try to finish
a closed plan and do not report its unticked boxes as open work.

What is actually outstanding lives in [`../backlog.md`](../backlog.md) (open modelling
questions) and in GitHub issues (tracked work). Settled decisions graduate into
[`../design/assumptions.md`](../design/assumptions.md); commit bodies carry the reasoning
trail.

## Why closed plans stay here

The sequencing in a plan dies when the work is done, but the *reasoning* — why a mechanism was
modelled this way, what was excluded and on what grounds — is the part worth keeping, and it is
hard to relocate without losing its context. So a plan is closed in place rather than deleted
or archived: the file and its published URL survive, and the header stops it reading as live
work. `AGENTS.md` § "Plans are closable" has the closing ritual.

## Opening a new one

Only when there is work that can actually start. A plan that lists blocked items is the
overhead this structure exists to avoid — if something is blocked on evidence or on a
decision, it belongs in the backlog until it is not.
