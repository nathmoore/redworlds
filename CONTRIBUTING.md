# Contributing

Contributions are welcome, and they are greatly appreciated! Every little bit helps, and credit will always be given.

**Before you write code, read [AGENTS.md](AGENTS.md)** — it is the working agreement for this repo (how to run it, code and testing standards, modelling discipline, what must never be committed to a public repo, and how commits are written). It is written for humans and AI assistants alike.

You can contribute in many ways:

## Types of Contributions

### Report Bugs

Report bugs at https://github.com/nathmoore/redworlds/issues.

If you are reporting a bug, please include:

- Your operating system name and version.
- Any details about your local setup that might be helpful in troubleshooting.
- Detailed steps to reproduce the bug.

### Fix Bugs

Look through the GitHub issues for bugs. Anything tagged with "bug" and "help wanted" is open to whoever wants to implement it.

### Implement Features

Look through the GitHub issues for features. Anything tagged with "enhancement" and "help wanted" is open to whoever wants to implement it.

### Write Documentation

Red Worlds could always use more documentation, whether as part of the official docs, in docstrings, or even on the web in blog posts, articles, and such.

To preview the docs locally:

```sh
just docs-serve
```

This starts a local server at http://localhost:8000 with live reload. Edit files in `docs/` or add docstrings to your code (the API reference page is auto-generated).

### Submit Feedback

The best way to send feedback is to file an issue at https://github.com/nathmoore/redworlds/issues.

If you are proposing a feature:

- Explain in detail how it would work.
- Keep the scope as narrow as possible, to make it easier to implement.
- Remember that this is a volunteer-driven project, and that contributions are welcome :)

## Get Started!

Ready to contribute? Here's how to set up `redworlds` for local development.

1. Fork the `redworlds` repo on GitHub.
2. Clone your fork locally:

   ```sh
   git clone git@github.com:your_name_here/redworlds.git
   ```

3. Install your local copy with uv:

   ```sh
   cd redworlds/
   uv sync
   ```

4. Create a branch for local development:

   ```sh
   git checkout -b name-of-your-bugfix-or-feature
   ```

   Now you can make your changes locally.

5. When you're done making changes, check that your changes pass linting and the tests:

   ```sh
   just qa
   ```

   Or run the tests alone:

   ```sh
   just test
   ```

6. Commit your changes and push your branch to GitHub:

   ```sh
   git add .
   git commit -m "Your detailed description of your changes."
   git push origin name-of-your-bugfix-or-feature
   ```

7. Submit a pull request through the GitHub website.

## Pull Request Guidelines

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. If the pull request adds functionality, the docs should be updated. Put your new functionality into a function with a docstring, and add the feature to the list in README.md.
3. The pull request should work for Python 3.12, 3.13, and 3.14. Tests run in GitHub Actions on every pull request to the main branch, make sure that the tests pass for all supported Python versions.

## Using an AI assistant

**Assistants are welcome here.** This repo is built with them and written to be legible to
them — `AGENTS.md` is the working agreement, and `docs/ai-guide.md` covers what the model can
be explained from a read and what needs an actual run. Using one is not something to
apologise for or hide.

Two things are asked of a contribution that used one, and neither is about the tool.

**Say that you did.** One line in the pull request is enough — which assistant, and roughly
how much of the change it wrote. This is not a disclaimer. It tells a reviewer where to look
hardest, in the same way "I'm new to input-output tables" would.

**Say what you checked yourself.** This is the one that matters. The risk with generated code
here is not malice, it is *confident wrongness* — plausible prose wrapped around a number
nobody verified. A model will write a beautifully-reasoned basket containing a product label
that does not exist, and explain its choice persuasively.

So for a modelling change, say which of these you did:

- Ran it against a real table, not only the pymrio test world.
- Checked a cited figure against its source rather than trusting the citation.
- Confirmed the result's *magnitude* is sane, not only that the code runs. An answer a
  million times out is often the one that looks most reasonable.

### What protects you, and what does not

The repo is built so that being wrong is usually caught by machine rather than by a reviewer's
expertise. A mistyped product label raises at load time, because `validate_baskets` checks
every basket against the table the tapes will actually run on. That is deliberate: in pandas,
a label that matches nothing selects nothing, so without the check a tape would silently score
zero and ship a plausible number.

What that catches is *invalid* input. What it cannot catch is a **well-formed number that is
wrong** — a defensible-looking ceiling with no source, a lifetime figure someone guessed. That
is why every number in `docs/design/tape_records.md` carries its basis and its source, and why
"what is your source?" is a fair question for any figure in a pull request, asked by someone
who does not know the sector.

Two habits follow, and they are the actual standard here:

- **A number without a source is not finished.** Order-of-magnitude is fine; *unstated* is not.
  Several figures in this repo are explicitly marked weak, which is what makes them safe to
  ship and easy to improve.
- **State the simplification.** If a change stands in for something more thorough, say so in
  the docstring and leave a backlog item. A simplification with a name is a decision; the same
  shortcut undocumented is technical debt.

### Changes to `AGENTS.md` and `CLAUDE.md`

These files are read as *instructions* by whatever assistant the next contributor brings, so a
change to them changes how other people's tooling behaves. They are owned in `CODEOWNERS` and
need maintainer review.

Improvements to them are genuinely wanted — this is a review requirement, not a closed door.
Propose them as their own pull request rather than folded into a code change, so the
instruction change is visible on its own.

## Tips

To run a subset of tests:

```sh
uv run pytest tests/
```

## Deploying

A reminder for the maintainers on how to deploy. Make sure all your changes are committed (including an entry in HISTORY.md). Then run:

```sh
uv version patch  # or: minor, major
git commit -am "Release X.Y.Z"
just tag
```

GitHub Actions will automatically publish to PyPI when the tag is pushed. See `.github/workflows/publish.yml` for details.

## Code of Conduct

Please note that this project is released with a [Contributor Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project you agree to abide by its terms.
