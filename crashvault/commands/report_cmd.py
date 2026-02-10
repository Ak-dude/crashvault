import click, json, os, uuid
from datetime import datetime, timezone
from ..core import event_path_for


@click.command(name="report")
@click.option("--title", required=True, help="Short report title")
@click.option("--body", required=False, default="", help="Detailed report body")
@click.option("--tag", "tags", multiple=True)
def report(title, body, tags):
    """Create a structured report entry (e.g., release note, incident summary)."""
    event_id = str(uuid.uuid4())
    ts = datetime.now(timezone.utc)
    data = {
        "event_id": event_id,
        "issue_id": -1,
        "message": title,
        "stacktrace": body,
        "timestamp": ts.isoformat().replace("+00:00", "Z"),
        "level": "info",
        "tags": list(tags) + ["report"],
        "context": {},
        "host": os.uname().nodename if hasattr(os, "uname") else os.getenv("COMPUTERNAME", "unknown"),
        "pid": os.getpid(),
    }
    path = event_path_for(event_id, ts)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)
    from ..rich_utils import get_console
    console = get_console()
    console.print(f"[success]Report[/success] [highlight]{event_id}[/highlight] [success]saved[/success]")


