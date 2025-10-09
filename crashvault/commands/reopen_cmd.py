import click
from ..core import load_issues, save_issues


@click.command()
@click.argument("issue_id", type=int)
def reopen(issue_id):
    """Reopen a resolved/ignored issue."""
    issues = load_issues()
    issue = next((i for i in issues if i["id"] == issue_id), None)
    if not issue:
        click.echo("Issue not found")
        return
    issue["status"] = "open"
    save_issues(issues)
    click.echo(f"Issue #{issue_id} reopened")


