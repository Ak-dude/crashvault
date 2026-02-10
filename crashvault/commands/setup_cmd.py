import click
from ..install_hook import create_user_config
from ..rich_utils import get_console

console = get_console()


@click.command(name="setup")
def setup_cmd():
    """Initialize or regenerate the .crashvault configuration directory."""
    config_dir = create_user_config()
    console.print(f"[success]Crashvault configuration initialized at[/success] [highlight]{config_dir}[/highlight]")
    console.print("\n[info]Edit ~/.crashvault/config.json to customize:[/info]")
    console.print("  [muted]-[/muted] User information (name, email, team)")
    console.print("  [muted]-[/muted] AI settings (provider, model, API key)")
    console.print("  [muted]-[/muted] Notification preferences")
    console.print("  [muted]-[/muted] Storage settings")
