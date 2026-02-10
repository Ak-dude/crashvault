import click, json
from ..core import load_issues, EVENTS_DIR
from ..rich_utils import get_console

console = get_console()


@click.command()
def gc():
    """Garbage collect orphaned events (without a valid issue)."""
    issues = load_issues()
    valid_ids = {i["id"] for i in issues}
    removed = 0
    for f in EVENTS_DIR.glob("**/*.json"):
        try:
            ev = json.loads(f.read_text())
        except Exception:
            try:
                f.unlink()
                removed += 1
            except Exception:
                pass
            continue
        if ev.get("issue_id") not in valid_ids:
            try:
                f.unlink()
                removed += 1
            except Exception:
                pass
    console.print(f"[success]Removed {removed} orphaned event file(s)[/success]")


