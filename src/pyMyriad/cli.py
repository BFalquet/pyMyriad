"""Command-line interface module.

This module provides a simple CLI for pyMyriad. Currently contains a placeholder
command for testing purposes.

The CLI can be extended to provide command-line access to pyMyriad's analysis
and reporting capabilities.
"""

import click


@click.command()
@click.argument("x", type=int)
def main(x: int):
    """Simple CLI test"""
    res = 10 * x
    click.echo(f"Result was {res}")
