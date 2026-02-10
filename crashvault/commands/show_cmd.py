import click, json
from ..core import load_issues, EVENTS_DIR
from ..rich_utils import get_console

console = get_console()


@click.command()
@click.argument("issue_id", type=int)
def show(issue_id):
    issues = load_issues()
    issue = next((i for i in issues if i["id"] == issue_id), None)
    if not issue:
        console.print("[error]Issue not found[/error]")
        return

    issue_status = issue['status']
    status_style = "success" if issue_status == "resolved" else "warning" if issue_status == "ignored" else "primary"
    console.print(f"[highlight]Issue #{issue['id']}:[/highlight] {issue['title']} [{status_style}]({issue_status})[/{status_style}]")

    for f in (EVENTS_DIR.glob("**/*.json")):
        ev = json.loads(f.read_text())
        if ev["issue_id"] == issue_id:
            level = ev.get('level', '').upper()
            level_style = "danger" if level in ["ERROR", "CRITICAL"] else "warning" if level == "WARNING" else "info"
            console.print(f"  [muted]-[/muted] [secondary]{ev['timestamp']}[/secondary] [{level_style}][{level}][/{level_style}] {ev['message']}")
            if ev["stacktrace"]:
                console.print(f"    [muted]Stack:[/muted] {ev['stacktrace']}")
            if ev.get("tags"):
                console.print(f"    [muted]Tags:[/muted] {', '.join(ev['tags'])}")


