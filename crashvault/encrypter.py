"""Encryption module for CrashVault encrypted vaults.

Uses Fernet symmetric encryption from the cryptography library.
"""
import os
import json
from pathlib import Path
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64


def _derive_key(password: str) -> bytes:
    """Derive a Fernet key from a password using PBKDF2."""
    salt = b"crashvault_salt_v1"  # Fixed salt for consistency
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key


def encrypt_data(data: bytes, password: str) -> bytes:
    """Encrypt data with a password."""
    key = _derive_key(password)
    f = Fernet(key)
    return f.encrypt(data)


def decrypt_data(data: bytes, password: str) -> bytes:
    """Decrypt data with a password. Raises InvalidToken if password is wrong."""
    key = _derive_key(password)
    f = Fernet(key)
    return f.decrypt(data)


def encrypt_file(file_path: Path, password: str) -> None:
    """Encrypt a JSON file in place."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    data = file_path.read_bytes()
    encrypted = encrypt_data(data, password)
    file_path.write_bytes(encrypted)


def decrypt_file(file_path: Path, password: str) -> bytes:
    """Decrypt an encrypted file and return the decrypted content."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    encrypted_data = file_path.read_bytes()
    return decrypt_data(encrypted_data, password)


def is_encrypted_file(file_path: Path) -> bool:
    """Check if a file appears to be encrypted (starts with Fernet token)."""
    if not file_path.exists():
        return False
    
    try:
        data = file_path.read_bytes()
        # Fernet tokens start with version byte (0x80) in base64
        # They are always a multiple of 4 bytes after base64 decoding
        # The actual token is URL-safe base64 encoded
        if len(data) < 32:  # Minimum Fernet token size
            return False
        # Try to decode as Fernet - if it works, it's encrypted
        key = b"x" * 32  # Dummy key, we just check format
        # We can't use Fernet directly without knowing the key
        # So check the format: base64 URL-safe, starts with specific byte
        return data[0] == 0x80 or data[0:4] == b'\x80\x02'  # Common Fernet prefixes
    except Exception:
        return False
