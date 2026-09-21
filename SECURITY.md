# Security

## Reporting a vulnerability

**Please do not open a public issue for a security problem.**

Use GitHub's private reporting instead: go to the
[Security tab](https://github.com/nathmoore/redworlds/security/advisories/new) and open a
draft advisory. That reaches the maintainer privately and gives us somewhere to talk before
anything is public.

This is a small project maintained by one person, so please be patient — expect a first reply
within about a week. If something is actively being exploited, say so in the title and it will
be picked up sooner.

## What is in scope

Red Worlds is a simulation library. It has no server, no user accounts and no network
listener, so the interesting surface is narrower than most projects. Things worth reporting:

- **Anything that executes code you did not expect** — from loading a config file, parsing a
  downloaded table, reading a concordance, or importing the package.
- **A supply-chain problem**: a dependency we pull in, or a GitHub Actions workflow that could
  be made to run untrusted code with repository permissions.
- **Anything that would let a pull request reach our PyPI release** without passing through
  the protected publish path.
- **Player data of any kind appearing in this repository.** It should never be here — the
  game is a separate private codebase and this repo models economies, not people. If you find
  some, that is a real finding however it got here.

## What is not a vulnerability

- **A wrong number.** If a ceiling is implausible or a basket is mis-specified, that is a bug
  and we want to hear about it — but in a public issue, please, where it can be argued with.
  Being wrong in the open is the point of the repo.
- **The model being a simplification.** It is one on purpose, and the simplifications are
  documented in `docs/design/assumptions.md`.

## Releases

The package publishes to PyPI from a tagged release through GitHub Actions, using
[trusted publishing](https://docs.pypi.org/trusted-publishers/) — a short-lived OIDC token
rather than a stored API key. There is no long-lived PyPI credential in this repository's
secrets to steal, and the publish job runs in a protected environment.

Workflows declare least-privilege permissions and pin third-party actions by commit SHA. If
you spot one that does not, that is worth reporting under the supply-chain heading above.
