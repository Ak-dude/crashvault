import click
from ..core import ISSUES_FILE, EVENTS_DIR
from ..rich_utils import get_console

console = get_console()

@click.command()
@click.confirmation_option(prompt="Are you sure you want to delete all logs?")
def kill():
    """Delete all issues and events (wipe logs)."""
    if ISSUES_FILE.exists():
        ISSUES_FILE.unlink()
    for f in EVENTS_DIR.glob("**/*.json"):
        f.unlink()
    console.print("[danger]All logs deleted![/danger]")


