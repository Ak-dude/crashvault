import click
from datetime import datetime, timezone
from ..core import EVENTS_DIR
from ..rich_utils import get_console

console = get_console()


@click.command(name="prune")
@click.option("--days", type=int, default=90, show_default=True, help="Remove events older than N days")
def prune(days):
    """Remove old events to save disk space."""
    cutoff = datetime.now(timezone.utc).timestamp() - (days * 86400)
    removed = 0
    for p in EVENTS_DIR.glob("**/*.json"):
        try:
            if p.stat().st_mtime < cutoff:
                p.unlink()
                removed += 1
        except Exception:
            continue
    console.print(f"[success]Pruned {removed} old event file(s)[/success]")


