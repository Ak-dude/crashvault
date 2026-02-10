import click
from ..core import load_issues, save_issues
from ..rich_utils import get_console

console = get_console()


@click.command()
@click.argument("issue_id", type=int)
def resolve(issue_id):
    issues = load_issues()
    issue = next((i for i in issues if i["id"] == issue_id), None)
    if not issue:
        console.print("[error]Issue not found[/error]")
        return
    issue["status"] = "resolved"
    save_issues(issues)
    console.print(f"[success]Issue[/success] [highlight]#{issue_id}[/highlight] [success]marked resolved[/success]")


