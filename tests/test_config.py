"""Tests for `redworlds.config`."""

from pathlib import Path

import pytest

from redworlds.config import _EXAMPLE_PATH, load_config


def test_loads_a_toml_file(tmp_path: Path):
    """A given config file is parsed into a nested dict."""
    config_file = tmp_path / "config.toml"
    config_file.write_text('[data]\nexiobase_path = "/somewhere/exiobase"\n')

    cfg = load_config(config_file)

    assert cfg["data"]["exiobase_path"] == "/somewhere/exiobase"


def test_missing_file_says_how_to_fix_it(tmp_path: Path):
    """A missing config file raises FileNotFoundError naming the example template."""
    with pytest.raises(FileNotFoundError, match="config.example.toml"):
        load_config(tmp_path / "nope.toml")


def test_example_template_parses():
    """The committed template is valid TOML with the keys the jobs expect."""
    cfg = load_config(_EXAMPLE_PATH)

    assert "exiobase_path" in cfg["data"]
    assert "capital_use_path" in cfg["data"]
    assert "worlds_path" in cfg["data"]
