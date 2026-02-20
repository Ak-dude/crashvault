"""Encryption commands for CrashVault."""
import click
from ..core import encrypt_vault, is_vault_encrypted, load_config
from ..rich_utils import get_console

console = get_console()


@click.command(name="encrypt")
@click.argument("password")
def encrypt_cmd(password):
    """Encrypt the current vault with a password.
    
    This will encrypt the issues.json file on disk. After encryption,
    you will need to provide the password each time you open the vault.
    """
    if is_vault_encrypted():
        console.print("[error]Vault is already encrypted![/error]")
        return
    
    encrypt_vault(password)
    console.print("[success]Vault has been encrypted successfully![/success]")
    console.print("\n[info]Important:[/info]")
    console.print("  - Keep your password safe - without it, your data cannot be recovered")
    console.print("  - You will need to provide the password each time you use crashvault")
    console.print("  - Use [highlight]crashvault decrypt <password>[/highlight] to decrypt the vault")
