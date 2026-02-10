import click
from ..core import load_events
from ..rich_utils import get_console

console = get_console()


@click.command(name="events")
@click.option("--issue", type=int, help="Only events for issue id")
@click.option("--limit", type=int, default=50, show_default=True)
@click.option("--offset", type=int, default=0, show_default=True)
def events_cmd(issue, limit, offset):
    """List events with optional pagination."""
    all_events = load_events()
    if issue is not None:
        all_events = [e for e in all_events if e.get("issue_id") == issue]
    all_events.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    page = all_events[offset: offset + limit]
    for ev in page:
        ev_level = ev.get('level', '').upper()
        level_style = "danger" if ev_level in ["ERROR", "CRITICAL"] else "warning" if ev_level == "WARNING" else "info"
        console.print(f"[secondary]{ev['timestamp']}[/secondary] [{level_style}][{ev_level}][/{level_style}] [highlight]#{ev['issue_id']}[/highlight] {ev['message']}")
    console.print(f"[muted]-- showing {len(page)} of {len(all_events)} --[/muted]")


