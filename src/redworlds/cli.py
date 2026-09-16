"""Console script for redworlds."""

from importlib.metadata import version

import typer
from rich.console import Console

app = typer.Typer()
console = Console()


@app.command()
def main() -> None:
    """Print the installed Red Worlds version and where to start."""
    console.print(f"Red Worlds {version('redworlds')}")
    console.print("Engine functions live in redworlds.engine; see docs/design/red_carbon_contract.md to start.")


if __name__ == "__main__":
    app()
