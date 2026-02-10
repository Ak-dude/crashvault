import click, json
from ..core import EVENTS_DIR
from ..rich_utils import get_console

console = get_console()


@click.command()
@click.option("--level", type=click.Choice(["debug","info","warning","error","critical"], case_sensitive=False), help="Filter by level")
@click.option("--tag", "tags", multiple=True, help="Filter by tag(s)")
@click.option("--text", default="", help="Search text in message")
def search(level, tags, text):
    """Search events with optional filters."""
    level = level.lower() if level else None
    count = 0
    for f in EVENTS_DIR.glob("**/*.json"):
        ev = json.loads(f.read_text())
        if level and ev.get("level") != level:
            continue
        if tags:
            etags = set(ev.get("tags", []))
            if not set(tags).issubset(etags):
                continue
        if text and text.lower() not in ev.get("message", "").lower():
            continue
        ev_level = ev.get('level', '').upper()
        level_style = "danger" if ev_level in ["ERROR", "CRITICAL"] else "warning" if ev_level == "WARNING" else "info"
        console.print(f"[secondary]{ev['timestamp']}[/secondary] [{level_style}][{ev_level}][/{level_style}] [highlight]#{ev['issue_id']}[/highlight] {ev['message']}")
        count += 1
    console.print(f"[muted]-- {count} event(s) matched --[/muted]")


