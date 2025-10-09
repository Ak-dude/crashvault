import click
from ..core import load_issues, save_issues


@click.command()
@click.argument("issue_id", type=int)
@click.argument("title")
def set_title(issue_id, title):
    """Rename an issue's title."""
    issues = load_issues()
    issue = next((i for i in issues if i["id"] == issue_id), None)
    if not issue:
        click.echo("Issue not found")
        return
    issue["title"] = title[:200]
    save_issues(issues)
    click.echo(f"Issue #{issue_id} title updated")


