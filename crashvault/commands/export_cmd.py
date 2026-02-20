import csv
import click, json
from datetime import datetime, timezone
from pathlib import Path
from ..core import load_issues, load_events
from ..rich_utils import get_console

console = get_console()


@click.command()
@click.option("--output", type=click.Path(dir_okay=False, writable=True, resolve_path=True), help="Output file (JSON/CSV). Defaults to stdout")
@click.option("--format", "export_format", type=click.Choice(["json", "csv"], case_sensitive=False), default="json", show_default=True, help="Export format")
def export(output, export_format):
    """Export all issues and events to JSON or CSV."""
    issues = load_issues()
    events = load_events()
    
    if export_format == "csv":
        # CSV export: combine issues and events into a flat table
        rows = []
        # Add issue rows
        for issue in issues:
            rows.append({
                "type": "issue",
                "id": issue.get("id", ""),
                "fingerprint": issue.get("fingerprint", ""),
                "title": issue.get("title", ""),
                "status": issue.get("status", ""),
                "created_at": issue.get("created_at", ""),
                "message": issue.get("title", ""),
                "level": "",
                "timestamp": issue.get("created_at", ""),
                "tags": ",".join(issue.get("tags", [])) if isinstance(issue.get("tags"), list) else "",
                "host": "",
            })
        # Add event rows
        for event in events:
            rows.append({
                "type": "event",
                "id": event.get("event_id", ""),
                "fingerprint": "",
                "title": "",
                "status": "",
                "created_at": "",
                "message": event.get("message", ""),
                "level": event.get("level", ""),
                "timestamp": event.get("timestamp", ""),
                "tags": ",".join(event.get("tags", [])) if isinstance(event.get("tags"), list) else "",
                "host": event.get("host", ""),
            })
        
        # Write CSV
        fieldnames = ["type", "id", "fingerprint", "title", "status", "created_at", "message", "level", "timestamp", "tags", "host"]
        output_io = __import__("io").StringIO()
        writer = csv.DictWriter(output_io, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)
        data = output_io.getvalue()
        
        if output:
            Path(output).write_text(data)
            console.print(f"[success]Exported to[/success] [highlight]{output}[/highlight]")
        else:
            click.echo(data)
    else:
        # JSON export (original behavior)
        payload = {
            "version": 1,
            "exported_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "issues": issues,
            "events": events,
        }
        data = json.dumps(payload, indent=2)
        if output:
            Path(output).write_text(data)
            console.print(f"[success]Exported to[/success] [highlight]{output}[/highlight]")
        else:
            click.echo(data)


