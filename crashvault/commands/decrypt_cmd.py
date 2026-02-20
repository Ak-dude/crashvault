"""Decryption commands for CrashVault."""
import click
from ..core import decrypt_vault, is_vault_encrypted
from ..rich_utils import get_console

console = get_console()


@click.command(name="decrypt")
@click.argument("password")
def decrypt_cmd(password):
    """Decrypt an encrypted vault with a password.
    
    This will decrypt the issues.json file on disk. After decryption,
    the vault will be stored as plain JSON.
    """
    if not is_vault_encrypted():
        console.print("[error]Vault is not encrypted![/error]")
        return
    
    try:
        decrypt_vault(password)
        console.print("[success]Vault has been decrypted successfully![/success]")
    except ValueError as e:
        console.print(f"[error]Decryption failed: {e}[/error]")
