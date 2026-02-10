import click, shutil
from pathlib import Path
from ..core import ATTACH_DIR
from ..rich_utils import get_console

console = get_console()


@click.command(name="attach")
@click.argument("file", type=click.Path(exists=True, dir_okay=False, readable=True, resolve_path=True))
@click.option("--name", help="Optional name under attachments/")
def attach(file, name):
    """Copy a file into Crashvault attachments for reference."""
    src = Path(file)
    dest = ATTACH_DIR / (name or src.name)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    console.print(f"[success]Attached[/success] [info]{src}[/info] [muted]->[/muted] [highlight]{dest}[/highlight]")


