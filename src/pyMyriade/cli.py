

import click

@click.command()
@click.argument("x", type = int)
def main(x: int):
    """Simple CLI test"""
    res = 10 * x
    click.echo(f"Result was {res}")