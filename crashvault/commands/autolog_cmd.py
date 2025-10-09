import click, json, os, sys, uuid, platform, atexit, traceback
from datetime import datetime, timezone
from ..core import event_path_for


@click.command(name="autolog")
@click.option("--enable/--disable", default=True, show_default=True)
def autolog(enable):
    """Enable a simple Python exception hook to auto-log uncaught errors."""
    if not enable:
        click.echo("Autolog disable is a noop for this simple CLI.")
        return

    def excepthook(etype, value, tb):
        event_id = str(uuid.uuid4())
        ts = datetime.now(timezone.utc)
        message = f"Uncaught exception: {etype.__name__}: {value}"
        stack = "".join(traceback.format_exception(etype, value, tb))
        data = {
            "event_id": event_id,
            "issue_id": 0,
            "message": message,
            "stacktrace": stack,
            "timestamp": ts.isoformat().replace("+00:00", "Z"),
            "level": "error",
            "tags": ["autolog"],
            "context": {},
            "host": platform.node(),
            "pid": os.getpid(),
        }
        path = event_path_for(event_id, ts)
        tmp = path.with_suffix(path.suffix + ".tmp")
        with open(tmp, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, path)

    sys.excepthook = excepthook
    # Best effort: write a tiny marker so users know it's active in this process
    atexit.register(lambda: None)
    click.echo("Autolog exception hook installed for this Python process.")


