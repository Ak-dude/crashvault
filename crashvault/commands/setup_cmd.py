"""Setup command for CrashVault."""
import click
from ..install_hook import create_user_config
from ..rich_utils import get_console
from ..core import create_encrypted_vault, ensure_dirs, ROOT

console = get_console()


@click.command(name="setup")
@click.option("--encrypted", is_flag=True, help="Create an encrypted vault")
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True, help="Password for encrypted vault")
def setup_cmd(encrypted, password):
    """Initialize or regenerate the .crashvault configuration directory.
    
    Use --encrypted to create an encrypted vault from the start.
    """
    config_dir = create_user_config()
    
    if encrypted:
        # Create encrypted vault
        ensure_dirs()
        create_encrypted_vault(password)
        console.print(f"[success]Encrypted Crashvault initialized at[/success] [highlight]{config_dir}[/highlight]")
        console.print("\n[warning]Vault is encrypted![/warning]")
        console.print("  - Keep your password safe - without it, your data cannot be recovered")
        console.print("  - You will need to provide the password each time you use crashvault")
    else:
        console.print(f"[success]Crashvault configuration initialized at[/success] [highlight]{config_dir}[/highlight]")
        console.print("\n[info]Edit ~/.crashvault/config.json to customize:[/info]")
        console.print("  [muted]-[/muted] User information (name, email, team)")
        console.print("  [muted]-[/muted] AI settings (provider, model, API key)")
        console.print("  [muted]-[/muted] Notification preferences")
        console.print("  [muted]-[/muted] Storage settings")
        
        console.print("\n[info]To create an encrypted vault, use:[/info]")
        console.print("  [highlight]crashvault setup --encrypted[/highlight]")
