import click, json
from ..core import load_issues, EVENTS_DIR


@click.command()
@click.argument("issue_id", type=int)
def show(issue_id):
    issues = load_issues()
    issue = next((i for i in issues if i["id"] == issue_id), None)
    if not issue:
        click.echo("Issue not found")
        return
    click.echo(f"Issue #{issue['id']}: {issue['title']} ({issue['status']})")
    for f in (EVENTS_DIR.glob("**/*.json")):
        ev = json.loads(f.read_text())
        if ev["issue_id"] == issue_id:
            click.echo(f"  - {ev['timestamp']} [{ev.get('level','').upper()}] {ev['message']}")
            if ev["stacktrace"]:
                click.echo(f"    Stack: {ev['stacktrace']}")
            if ev.get("tags"):
                click.echo(f"    Tags: {', '.join(ev['tags'])}")


