import click, json, re
from pathlib import Path
from ..core import EVENTS_DIR
from ..rich_utils import get_console

console = get_console()

_STACK_RE = re.compile(r"File \"(?P<file>.+?)\", line (?P<line>\d+)")


def _extract_frames(stack: str):
    frames = []
    for m in _STACK_RE.finditer(stack):
        try:
            frames.append((Path(m.group("file")), int(m.group("line"))))
        except Exception:
            continue
    return frames


def _read_context(path: Path, line: int, radius: int = 5):
    if not path.exists():
        return None
    lines = path.read_text(errors="ignore").splitlines()
    start = max(1, line - radius)
    end = min(len(lines), line + radius)
    ctx = []
    for idx in range(start, end + 1):
        prefix = ">" if idx == line else " "
        ctx.append(f"{prefix}{idx:5d}: {lines[idx-1]}")
    return "\n".join(ctx)


@click.command(name="diagnose")
@click.argument("event_id")
def diagnose(event_id):
    """Show source code context for an event's stack trace."""
    event_file = None
    for p in EVENTS_DIR.glob("**/*.json"):
        if p.stem == event_id:
            event_file = p
            break
    if not event_file:
        raise click.ClickException("Event not found")
    ev = json.loads(event_file.read_text())
    stack = ev.get("stacktrace", "")
    if not stack:
        console.print("[warning]No stacktrace available for this event[/warning]")
        return
    frames = _extract_frames(stack)
    if not frames:
        console.print("[warning]Could not parse file/line frames from stacktrace[/warning]")
        return
    for path, line in frames:
        console.print(f"\n[highlight]--- {path} : line {line} ---[/highlight]")
        ctx = _read_context(path, line)
        if ctx:
            click.echo(ctx)
        else:
            console.print("[muted](file not found)[/muted]")


