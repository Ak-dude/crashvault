import click, subprocess, json, os, uuid, platform
from datetime import datetime, timezone
from ..core import event_path_for
from ..rich_utils import get_console

console = get_console()


@click.command(name="wrap")
@click.argument("cmd", nargs=-1)
@click.option("--level", default="error")
@click.option("--tag", "tags", multiple=True)
@click.option("--exit-code", "exit_codes", multiple=True, type=int, help="Only log errors with these exit codes (default: all non-zero)")
@click.option("--ignore-tag", "ignore_tags", multiple=True, help="Ignore events with these tags")
def wrap(cmd, level, tags, exit_codes, ignore_tags):
    """Run a subprocess; if it fails, auto-log the error event."""
    if not cmd:
        raise click.UsageError("Provide a command to run")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode == 0:
        click.echo(proc.stdout, nl=False)
        return
    
    # Filter by exit code if specified
    if exit_codes and proc.returncode not in exit_codes:
        click.echo(f"Command failed (exit {proc.returncode}) but exit code not in capture list", nl=False)
        if proc.stdout:
            click.echo(proc.stdout, nl=False)
        if proc.stderr:
            click.echo(proc.stderr, nl=False)
        raise SystemExit(proc.returncode)
    
    # on failure, log
    event_id = str(uuid.uuid4())
    ts = datetime.now(timezone.utc)
    message = f"Command failed: {' '.join(cmd)} (exit {proc.returncode})"
    event_tags = list(tags) + ["wrap"]
    
    # Filter by ignore tags
    if ignore_tags:
        matched_ignore = [t for t in event_tags if t in ignore_tags]
        if matched_ignore:
            console.print(f"[muted]Command failed but ignored by tag: {matched_ignore}[/muted]")
            if proc.stdout:
                click.echo(proc.stdout, nl=False)
            if proc.stderr:
                click.echo(proc.stderr, nl=False)
            raise SystemExit(proc.returncode)
    
    data = {
        "event_id": event_id,
        "issue_id": 0,
        "message": message,
        "stacktrace": (proc.stderr or "").strip(),
        "timestamp": ts.isoformat().replace("+00:00", "Z"),
        "level": level.lower(),
        "tags": event_tags,
        "context": {"returncode": proc.returncode},
        "host": platform.node(),
        "pid": os.getpid(),
    }
    path = event_path_for(event_id, ts)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)
    console.print(f"[error]{message}[/error]")
    if proc.stdout:
        click.echo(proc.stdout, nl=False)
    if proc.stderr:
        click.echo(proc.stderr, nl=False)
    raise SystemExit(proc.returncode)


