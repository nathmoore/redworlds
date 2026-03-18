"""Configuration loader for Red Worlds.

Reads config/config.toml (gitignored, personal) using config/config.example.toml
as the reference template. Raises a clear error if the file is missing.

Usage:
    from redworlds.config import load_config
    cfg = load_config()
    exiobase_path = cfg["data"]["exiobase_path"]
"""

from pathlib import Path

# Resolve config path relative to repo root (two levels up from this file's package)
_REPO_ROOT = Path(__file__).parent.parent.parent
_CONFIG_PATH = _REPO_ROOT / "config" / "config.toml"
_EXAMPLE_PATH = _REPO_ROOT / "config" / "config.example.toml"


def load_config(path: Path | None = None) -> dict:
    """Load configuration from a TOML file.

    Args:
        path: Path to the config file. Defaults to config/config.toml in the repo root.

    Returns:
        Parsed configuration as a nested dict.

    Raises:
        FileNotFoundError: If the config file does not exist, with instructions to
            copy config.example.toml.
    """
    # TODO: implement — see GitHub issue #1
    raise NotImplementedError
