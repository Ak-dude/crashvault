import click
from ..core import load_issues, save_issues
from ..rich_utils import get_console

console = get_console()


@click.command()
@click.argument("issue_id", type=int)
@click.argument("title")
def set_title(issue_id, title):
    """Rename an issue's title."""
    issues = load_issues()
    issue = next((i for i in issues if i["id"] == issue_id), None)
    if not issue:
        console.print("[error]Issue not found[/error]")
        return
    issue["title"] = title[:200]
    save_issues(issues)
    console.print(f"[success]Issue[/success] [highlight]#{issue_id}[/highlight] [success]title updated[/success]")


