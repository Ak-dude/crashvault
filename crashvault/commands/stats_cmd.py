import click, json
from ..core import load_issues, EVENTS_DIR


@click.command()
def stats():
    """Show simple statistics about issues and events."""
    issues = load_issues()
    status_counts = {"open": 0, "resolved": 0}
    for i in issues:
        status_counts[i.get("status", "open")] = status_counts.get(i.get("status", "open"), 0) + 1
    level_counts = {}
    for f in EVENTS_DIR.glob("**/*.json"):
        ev = json.loads(f.read_text())
        lvl = ev.get("level", "unknown")
        level_counts[lvl] = level_counts.get(lvl, 0) + 1
    click.echo("Issues by status:")
    for k, v in status_counts.items():
        click.echo(f"  {k}: {v}")
    click.echo("Events by level:")
    for k, v in sorted(level_counts.items()):
        click.echo(f"  {k}: {v}")


