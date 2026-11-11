# Installation

## Stable release

To install Red Worlds, run this command in your terminal:

```sh
uv add redworlds
```

Or if you prefer to use `pip`:

```sh
pip install redworlds
```

## From source

The source files for Red Worlds can be downloaded from the [Github repo](https://github.com/nathmoore/redworlds).

You can either clone the public repository:

```sh
git clone https://github.com/nathmoore/redworlds
```

Or download the [tarball](https://github.com/nathmoore/redworlds/tarball/main):

```sh
curl -OJL https://github.com/nathmoore/redworlds/tarball/main
```

Once you have a copy of the source, you can install it with:

```sh
cd redworlds
uv sync
```

## Setting up to run the engine

Installing the package is enough to read the code and run the default tests. Running the
engine on real data takes four more steps.

**1. Tools.** [uv](https://docs.astral.sh/uv/) manages Python and the dependencies;
[just](https://just.systems) runs the project's commands. Install both, then check:

```sh
uv --version
just --version
```

Without `just`, every recipe in the `justfile` can be run by hand — each is one `uv run`
line.

**2. A green test run.** No data needed; this proves the clone works.

```sh
uv sync
just test
```

**3. The data.** `data/README.md` has the downloads and where to put them: the EXIOBASE
3.8.2 table for 2011 (about 1.9 GB unpacked), its capital use matrix, and, for the baseline
walk, Ember's electricity data (16 MB). All three stay out of git.

**4. Your paths.** Copy `config/config.example.toml` to `config/config.toml` and point it at
the downloads and at a folder for cached worlds. Then:

```sh
just baseline               # parse, aggregate and cache the 2011 baseline: minutes
just export-tapes           # solve the tapes against it
just prepare-electricity    # rebuild the walk's electricity tables from the Ember download
just hindcast-electricity   # run the electricity-only walk
```

**How long things take.** It depends heavily on the machine. On an older 8 GB laptop the
default tests have taken a quarter of an hour, the baseline build several minutes and one
electricity hindcast about nine minutes; a current machine runs the tests in about a minute. A machine
with more memory is markedly faster, because the work is dominated by copying and inverting
large matrices.

### Moving to another machine

Three things are not in the repository and do not come with a fresh clone:

- `config/config.toml`, which holds absolute paths and must match the new machine;
- the downloads under `data/exiobase/` and `data/ember/`;
- the cached worlds under your `worlds_path`, which can be rebuilt with `just baseline`.

Copying the whole project folder brings all three. Cloning from GitHub brings none of them,
and brings only the commits that have been pushed.
