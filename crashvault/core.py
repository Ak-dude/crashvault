from pathlib import Path
import os, json, logging, platform, base64
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from cryptography.fernet import InvalidToken

from . import encrypter

ENV_ROOT = os.environ.get("CRASHVAULT_HOME")
ROOT = Path(ENV_ROOT) if ENV_ROOT else Path(os.path.expanduser("~/.crashvault"))
ISSUES_FILE = ROOT / "issues.json"
EVENTS_DIR = ROOT / "events"
LOGS_DIR = ROOT / "logs"
CONFIG_FILE = ROOT / "config.json"
ATTACH_DIR = ROOT / "attachments"

# Global encryption password (set when vault is opened)
_vault_password = None


def set_vault_password(password: str):
    """Set the vault password for encrypted vault operations."""
    global _vault_password
    _vault_password = password


def clear_vault_password():
    """Clear the vault password from memory."""
    global _vault_password
    _vault_password = None


def get_vault_password():
    """Get the current vault password."""
    return _vault_password


def is_vault_encrypted() -> bool:
    """Check if the vault is configured as encrypted."""
    cfg = load_config()
    return cfg.get("encrypted", False)


def _is_encrypted_json_file(file_path: Path) -> bool:
    """Check if a JSON file is actually encrypted (Fernet format)."""
    if not file_path.exists():
        return False
    try:
        data = file_path.read_bytes()
        # Check minimum size for Fernet token
        if len(data) < 32:
            return False
        # Check for Fernet token magic bytes (base64-decoded version byte 0x80)
        # The token is URL-safe base64, so first byte after decoding is 0x80
        # We can detect by checking if it starts with common base64 chars for Fernet
        # Fernet tokens start with version byte (0x80) after base64 decode
        # Simplified check: try to parse as JSON - if fails, might be encrypted
        try:
            json.loads(data)
            return False
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Check if it looks like base64 data (Fernet tokens are valid base64)
            try:
                decoded = base64.urlsafe_b64decode(data[:min(len(data), 44)])
                # If it decodes and looks like it has the Fernet version byte
                return len(decoded) >= 1 and decoded[0] == 0x80
            except Exception:
                return False
    except Exception:
        return False


def ensure_dirs():
    ROOT.mkdir(parents=True, exist_ok=True)
    EVENTS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    ATTACH_DIR.mkdir(parents=True, exist_ok=True)
    if not ISSUES_FILE.exists():
        ISSUES_FILE.write_text("[]")
    if not CONFIG_FILE.exists():
        _write_json_atomic(CONFIG_FILE, {"version": 1})


def configure_logging():
    logger = logging.getLogger("crashvault")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    log_path = LOGS_DIR / "app.log"
    handler = RotatingFileHandler(log_path, maxBytes=1024 * 1024, backupCount=3)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def _write_json_atomic(path: Path, data):
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with open(tmp_path, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp_path, path)


def _event_day_dir(ts: datetime) -> Path:
    day_dir = EVENTS_DIR / ts.strftime("%Y/%m/%d")
    day_dir.mkdir(parents=True, exist_ok=True)
    return day_dir


def event_path_for(event_id: str, ts: datetime) -> Path:
    return _event_day_dir(ts) / f"{event_id}.json"


def load_issues():
    ensure_dirs()
    if is_vault_encrypted() and _vault_password:
        # Encrypted vault
        if _is_encrypted_json_file(ISSUES_FILE):
            try:
                decrypted = encrypter.decrypt_file(ISSUES_FILE, _vault_password)
                return json.loads(decrypted)
            except InvalidToken:
                raise ValueError("Invalid password for encrypted vault")
        else:
            # Vault was just encrypted, file is not yet encrypted
            pass
    
    with open(ISSUES_FILE, "r") as f:
        return json.load(f)


def save_issues(issues):
    if is_vault_encrypted() and _vault_password:
        # Encrypt and save
        data = json.dumps(issues, indent=2).encode()
        encrypted = encrypter.encrypt_data(data, _vault_password)
        tmp_path = ISSUES_FILE.with_suffix(ISSUES_FILE.suffix + ".tmp")
        tmp_path.write_bytes(encrypted)
        os.replace(tmp_path, ISSUES_FILE)
    else:
        _write_json_atomic(ISSUES_FILE, issues)


def load_events():
    ensure_dirs()
    events = []
    for f in EVENTS_DIR.glob("**/*.json"):
        try:
            ev = json.loads(f.read_text())
            events.append(ev)
        except Exception:
            continue
    return events


def load_config():
    ensure_dirs()
    try:
        return json.loads(CONFIG_FILE.read_text())
    except Exception:
        return {"version": 1}


def save_config(cfg):
    _write_json_atomic(CONFIG_FILE, cfg)


def get_config_value(key, default=None):
    cfg = load_config()
    return cfg.get(key, default)


def get_user_config():
    """Get user configuration."""
    cfg = load_config()
    return cfg.get("user", {
        "name": os.getenv("USERNAME") or os.getenv("USER", "Unknown"),
        "email": "",
        "team": ""
    })


def encrypt_vault(password: str):
    """Encrypt the current vault with a password."""
    global _vault_password
    _vault_password = password
    
    # Update config to mark as encrypted
    cfg = load_config()
    cfg["encrypted"] = True
    save_config(cfg)
    
    # Encrypt issues file if it exists and is not already encrypted
    if ISSUES_FILE.exists() and not _is_encrypted_json_file(ISSUES_FILE):
        data = ISSUES_FILE.read_bytes()
        if data.strip():  # Only encrypt if not empty
            encrypted = encrypter.encrypt_data(data, password)
            ISSUES_FILE.write_bytes(encrypted)


def decrypt_vault(password: str):
    """Decrypt the vault with a password."""
    global _vault_password
    
    # Try to decrypt issues file
    if ISSUES_FILE.exists() and _is_encrypted_json_file(ISSUES_FILE):
        try:
            decrypted = encrypter.decrypt_file(ISSUES_FILE, password)
            # Write decrypted content back
            ISSUES_FILE.write_bytes(decrypted)
        except InvalidToken:
            raise ValueError("Invalid password for encrypted vault")
    
    # Update config to mark as not encrypted
    cfg = load_config()
    cfg["encrypted"] = False
    save_config(cfg)
    
    # Set the password temporarily so operations can complete
    _vault_password = password


def create_encrypted_vault(password: str):
    """Create a new vault that is encrypted from the start."""
    global _vault_password
    _vault_password = password
    
    ensure_dirs()
    
    # Create empty encrypted issues file
    data = json.dumps([], indent=2).encode()
    encrypted = encrypter.encrypt_data(data, password)
    ISSUES_FILE.write_bytes(encrypted)
    
    # Update config
    cfg = load_config()
    cfg["encrypted"] = True
    save_config(cfg)
