import click
from ..core import load_issues, save_issues
from ..rich_utils import get_console

console = get_console()


@click.command()
@click.argument("issue_id", type=int)
@click.argument("status", type=click.Choice(["open", "resolved", "ignored"], case_sensitive=False))
def set_status(issue_id, status):
    """Set an issue's status (open|resolved|ignored)."""
    issues = load_issues()
    issue = next((i for i in issues if i["id"] == issue_id), None)
    if not issue:
        console.print("[error]Issue not found[/error]")
        return
    issue["status"] = status.lower()
    save_issues(issues)
    status_style = "success" if status == "resolved" else "warning" if status == "ignored" else "primary"
    console.print(f"[success]Issue[/success] [highlight]#{issue_id}[/highlight] [success]status set to[/success] [{status_style}]{status}[/{status_style}]")


