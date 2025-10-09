import click
from ..core import ensure_dirs, ROOT


@click.command()
def init():
    """Create the Crashvault data folder structure if missing."""
    ensure_dirs()
    click.echo(str(ROOT))


@click.command()
def path():
    """Show the current Crashvault data path."""
    ensure_dirs()
    click.echo(str(ROOT))


