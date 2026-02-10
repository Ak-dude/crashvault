import click
from ..core import ensure_dirs, ROOT
from ..rich_utils import get_console

console = get_console()


@click.command()
def init():
    """Create the Crashvault data folder structure if missing."""
    ensure_dirs()
    console.print(f"[success]Initialized Crashvault at[/success] [highlight]{ROOT}[/highlight]")


@click.command()
def path():
    """Show the current Crashvault data path."""
    ensure_dirs()
    console.print(f"[info]{ROOT}[/info]")


