import click, json
from datetime import datetime, timezone
from pathlib import Path
from ..core import load_issues, load_events


@click.command()
@click.option("--output", type=click.Path(dir_okay=False, writable=True, resolve_path=True), help="Output file (JSON). Defaults to stdout")
def export(output):
    """Export all issues and events to JSON."""
    payload = {
        "version": 1,
        "exported_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "issues": load_issues(),
        "events": load_events(),
    }
    data = json.dumps(payload, indent=2)
    if output:
        Path(output).write_text(data)
        click.echo(f"Exported to {output}")
    else:
        click.echo(data)


