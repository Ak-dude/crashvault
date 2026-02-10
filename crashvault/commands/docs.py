import click, shutil
from ..rich_utils import get_console

console = get_console()


@click.command(name="docs")
def docs():
    """Open the Crashvault documentation."""
    url = "https://github.com/arkattaholdings/crashvault?tab=readme-ov-file#crashvault"
    console.print(f"[info]Opening documentation:[/info] [highlight]{url}[/highlight]")
    click.launch(url)