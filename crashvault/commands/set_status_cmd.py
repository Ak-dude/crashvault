import click
from ..core import load_issues, save_issues


@click.command()
@click.argument("issue_id", type=int)
@click.argument("status", type=click.Choice(["open", "resolved", "ignored"], case_sensitive=False))
def set_status(issue_id, status):
    """Set an issue's status (open|resolved|ignored)."""
    issues = load_issues()
    issue = next((i for i in issues if i["id"] == issue_id), None)
    if not issue:
        click.echo("Issue not found")
        return
    issue["status"] = status.lower()
    save_issues(issues)
    click.echo(f"Issue #{issue_id} status set to {status}")


