import click
from ..core import load_events


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
        click.echo(f"{ev['timestamp']} [{ev.get('level','').upper()}] #{ev['issue_id']} {ev['message']}")
    click.echo(f"-- showing {len(page)} of {len(all_events)} --")


