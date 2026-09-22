# Plans

Numbered implementation plans: scaffolding for a bounded piece of work, written so a session
can pick it up and act. **They are not a record of what is outstanding.**

| Plan | Status | Intent |
|---|---|---|
| [01 — Spike sprint](01-spike-sprint.md) | Closed 2026-09-22 | First numbers out of the real model, cheapest path first |
| [02 — Tape completion](02-tape-completion.md) | Closed 2026-09-22 | Nine tapes with real numbers and covers sized to the peg |

## The header

Every plan opens with four things, and the split between them is the point:

- **Designer intent** — Nathan's, one or two sentences. What he wanted out of it.
- **Success criteria** — the observable conditions that satisfy that intent.
- **Outcome** — met, partially met, or abandoned, once closed.
- **Added rigour (agent)** — structure, gates and checks an assistant added. These *serve* the
  intent; they do not extend it. An item here that stops serving the intent is dropped with a
  reason rather than carried as debt.

**Closure is a question about the intent, not a box count.** "Is the intent met?" has an
answer; "are all the boxes ticked?" does not, because an assistant can always add another box.
Nathan calls it. An assistant's job is to say, specifically, if the intent is *not* yet met —
not to defend the document's scope against him.

## Deferred topics

A closed plan keeps a short bulleted list of what it did not resolve, one line each, written
so a line can be pasted into a new conversation as a starting prompt. The backlog holds the
*authority* for those items; the plan holds the *situational memory* — what else was in play
when the question came up, and why it was parked. Both, because a backlog entry alone loses
the context that makes it easy to pick up again.

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
