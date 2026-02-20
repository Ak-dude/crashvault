import click, json, csv
from datetime import datetime, timezone
from pathlib import Path
from ..core import load_issues, load_events
from ..rich_utils import get_console

console = get_console()


def issues_to_csv(issues, writer):
    """Write issues to CSV format."""
    fieldnames = ["id", "title", "status", "created_at", "resolved_at", "event_count", "tags"]
    writer.writeheader()
    for issue in issues:
        row = {
            "id": issue.get("id", ""),
            "title": issue.get("title", ""),
            "status": issue.get("status", ""),
            "created_at": issue.get("created_at", ""),
            "resolved_at": issue.get("resolved_at", ""),
            "event_count": len(issue.get("events", [])),
            "tags": ", ".join(issue.get("tags", [])),
        }
        writer.writerow(row)


def events_to_csv(events, writer):
    """Write events to CSV format."""
    fieldnames = ["id", "issue_id", "message", "level", "timestamp", "source", "tags", "context"]
    writer.writeheader()
    for event in events:
        row = {
            "id": event.get("id", ""),
            "issue_id": event.get("issue_id", ""),
            "message": event.get("message", ""),
            "level": event.get("level", ""),
            "timestamp": event.get("timestamp", ""),
            "source": event.get("source", ""),
            "tags": ", ".join(event.get("tags", [])),
            "context": json.dumps(event.get("context", {})),
        }
        writer.writerow(row)


def export_as_csv(issues, events, output_path):
    """Export issues and events to CSV format."""
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        # Write issues section
        f.write("# Issues\n")
        issues_writer = csv.DictWriter(f, fieldnames=["id", "title", "status", "created_at", "resolved_at", "event_count", "tags"])
        issues_to_csv(issues, issues_writer)
        
        # Write blank line separator
        f.write("\n")
        
        # Write events section
        f.write("# Events\n")
        events_writer = csv.DictWriter(f, fieldnames=["event_id", "issue_id", "message", "level", "timestamp", "source", "tags", "context"])
        events_to_csv(events, events_writer)


@click.command()
@click.option("--output", type=click.Path(dir_okay=False, writable=True, resolve_path=True), help="Output file. Defaults to stdout")
@click.option("--format", type=click.Choice(["json", "csv"], case_sensitive=False), default="json", help="Export format (json or csv)")
def export(output, format):
    """Export all issues and events to JSON or CSV format."""
    issues = load_issues()
    events = load_events()
    
    if format == "csv":
        if not output:
            # Cannot output CSV to stdout with proper formatting, require output file
            console.print("[error]CSV format requires an output file. Use --output <filename>[/error]")
            return
        
        export_as_csv(issues, events, output)
        console.print(f"[success]Exported to[/success] [highlight]{output}[/highlight]")
    
    else:  # JSON format (default)
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
