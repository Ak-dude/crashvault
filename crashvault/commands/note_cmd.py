import click, json, os, uuid
from datetime import datetime, timezone
from ..core import event_path_for


@click.command(name="note")
@click.argument("message")
@click.option("--tag", "tags", multiple=True)
def note(message, tags):
    """Add a free-form note event (not just errors)."""
    event_id = str(uuid.uuid4())
    ts = datetime.now(timezone.utc)
    data = {
        "event_id": event_id,
        "issue_id": 0,
        "message": message,
        "stacktrace": "",
        "timestamp": ts.isoformat().replace("+00:00", "Z"),
        "level": "info",
        "tags": list(tags) + ["note"],
        "context": {},
        "host": os.uname().nodename if hasattr(os, "uname") else os.getenv("COMPUTERNAME", "unknown"),
        "pid": os.getpid(),
    }
    path = event_path_for(event_id, ts)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)
    click.echo(f"Note {event_id} saved")


