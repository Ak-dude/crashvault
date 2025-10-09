import click
from ..core import load_issues


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
        click.echo(f"#{i['id']} {i['title']} ({i['status']})")


