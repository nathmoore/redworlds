# CLAUDE.md — Red Worlds

**Read [`AGENTS.md`](AGENTS.md) first. It is the working agreement for this repo** — what
the project is, how to run it, code and testing standards, modelling discipline, what may
and may not be committed to a public repo, and how commits are written.

This file exists because Claude Code loads it automatically and would otherwise miss that
one. It deliberately duplicates nothing. If a rule needs changing, change it in
`AGENTS.md`.

Claude-specific notes:

- The repo is tool-neutral by design. Contributors arrive with Codex, Cursor, Copilot,
  Gemini or Claude Code, and nothing here should assume which. Write guidance that reads
  the same whichever one is holding it.
- If the task is understanding or explaining the model rather than changing it, start at
  [`docs/ai-guide.md`](docs/ai-guide.md) — it covers what this repo can answer from a
  read, what needs the engine run, and the mistakes an assistant reliably makes here.
- Commit attribution: name the model, per `AGENTS.md` § Git commits.
