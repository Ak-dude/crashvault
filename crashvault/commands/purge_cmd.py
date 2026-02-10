import click, json
from ..core import load_issues, save_issues, EVENTS_DIR
from ..rich_utils import get_console

console = get_console()


@click.command()
@click.argument("issue_id", type=int)
@click.confirmation_option(prompt="Delete this issue and all of its events?")
def purge(issue_id):
    """Delete one issue and all related events."""
    issues = load_issues()
    before = len(issues)
    issues = [i for i in issues if i["id"] != issue_id]
    if len(issues) == before:
        console.print("[error]Issue not found[/error]")
        return
    save_issues(issues)
    removed_events = 0
    for f in EVENTS_DIR.glob("**/*.json"):
        try:
            ev = json.loads(f.read_text())
        except Exception:
            continue
        if ev.get("issue_id") == issue_id:
            try:
                f.unlink()
                removed_events += 1
            except Exception:
                pass
    console.print(f"[danger]Purged issue[/danger] [highlight]#{issue_id}[/highlight] [danger]and {removed_events} event(s)[/danger]")


