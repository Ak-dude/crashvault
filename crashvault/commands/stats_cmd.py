import click, json
from ..core import load_issues, EVENTS_DIR
from ..rich_utils import get_console

console = get_console()


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

    console.print("[highlight]Issues by status:[/highlight]")
    for k, v in status_counts.items():
        status_style = "success" if k == "resolved" else "warning" if k == "ignored" else "primary"
        console.print(f"  [{status_style}]{k}:[/{status_style}] {v}")

    console.print("\n[highlight]Events by level:[/highlight]")
    for k, v in sorted(level_counts.items()):
        level_style = "danger" if k in ["error", "critical"] else "warning" if k == "warning" else "info"
        console.print(f"  [{level_style}]{k}:[/{level_style}] {v}")


