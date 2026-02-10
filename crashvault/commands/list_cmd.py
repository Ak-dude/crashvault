import click
from ..core import load_issues
from ..rich_utils import get_console

console = get_console()


@click.command(name="list")
@click.option("--status", type=click.Choice(["open", "resolved", "ignored"], case_sensitive=False), help="Filter by status")
@click.option("--sort", type=click.Choice(["id", "title", "status", "created_at"], case_sensitive=False), default="id", show_default=True)
@click.option("--desc/--asc", default=False, show_default=True)
def list_cmd(status, sort, desc):
    issues = load_issues()
    if status:
        issues = [i for i in issues if i.get("status") == status]
    key = sort
    issues.sort(key=lambda i: i.get(key) if key != "id" else int(i.get("id", 0)), reverse=bool(desc))
    for i in issues:
        issue_status = i['status']
        status_style = "success" if issue_status == "resolved" else "warning" if issue_status == "ignored" else "primary"
        console.print(f"[highlight]#{i['id']}[/highlight] {i['title']} [{status_style}]({issue_status})[/{status_style}]")


