import click
from .list_cmd import list_cmd
from .purge_cmd import purge
from .add_cmd import add
from .set_status_cmd import set_status
from .set_title_cmd import set_title
from .show_cmd import show


@click.command(name="ls")
@click.option("--status", type=click.Choice(["open", "resolved", "ignored"], case_sensitive=False))
def ls(status):
    ctx = click.get_current_context()
    ctx.invoke(list_cmd, status=status, sort="id", desc=False)


@click.command(name="rm")
@click.argument("issue_id", type=int)
def rm(issue_id):
    ctx = click.get_current_context()
    ctx.invoke(purge, issue_id=issue_id)


@click.command(name="new")
@click.argument("message")
def new(message):
    ctx = click.get_current_context()
    ctx.invoke(add, message=message, stack="", level="error", tags=(), contexts=())


@click.command(name="st")
@click.argument("issue_id", type=int)
@click.argument("status", type=click.Choice(["open", "resolved", "ignored"], case_sensitive=False))
def st(issue_id, status):
    ctx = click.get_current_context()
    ctx.invoke(set_status, issue_id=issue_id, status=status)


@click.command(name="title")
@click.argument("issue_id", type=int)
@click.argument("title")
def title_cmd(issue_id, title):
    ctx = click.get_current_context()
    ctx.invoke(set_title, issue_id=issue_id, title=title)


@click.command(name="sh")
@click.argument("issue_id", type=int)
def sh(issue_id):
    ctx = click.get_current_context()
    ctx.invoke(show, issue_id=issue_id)


