"""Post-install hook to set up user configuration."""
import os
import json
from pathlib import Path


def create_user_config():
    """Create .crashvault directory and default config in user's home."""
    home = Path.home()
    crashvault_dir = home / ".crashvault"
    
    # Create directory structure
    crashvault_dir.mkdir(exist_ok=True)
    (crashvault_dir / "events").mkdir(exist_ok=True)
    (crashvault_dir / "logs").mkdir(exist_ok=True)
    (crashvault_dir / "attachments").mkdir(exist_ok=True)
    
    # Create or update config file
    config_file = crashvault_dir / "config.json"
    default_config = {
        "version": 1,
        "user": {
            "name": os.getenv("USERNAME") or os.getenv("USER", "Unknown"),
            "email": "",
            "team": ""
        },
        "ai": {
            "provider": "ollama",  # ollama, openai, anthropic, gemini
            "model": "qwen2.5-coder:7b",
            "api_key": "",
            "base_url": "http://localhost:11434",  # for ollama
            "gemini": {
                "api_key": "",
                "model": "gemini-1.5-pro"
            }
        },
        "notifications": {
            "enabled": True,
            "on_error": True,
            "on_critical": True
        },
        "storage": {
            "max_events_per_day": 1000,
            "retention_days": 90,
            "compress_old_events": False
        }
    }
    
    if config_file.exists():
        # Merge with existing config, preserving user settings
        try:
            with open(config_file, 'r') as f:
                existing_config = json.load(f)
            
            # Update default config with existing values
            for key, value in existing_config.items():
                if isinstance(value, dict) and key in default_config:
                    default_config[key].update(value)
                else:
                    default_config[key] = value
        except Exception:
            pass  # If we can't read existing config, use defaults
    
    with open(config_file, 'w') as f:
        json.dump(default_config, f, indent=2)
    
    print(f"Updated Crashvault config at {config_file}")
    print("Edit ~/.crashvault/config.json to customize your settings")
    
    # Create issues.json if it doesn't exist
    issues_file = crashvault_dir / "issues.json"
    if not issues_file.exists():
        with open(issues_file, 'w') as f:
            json.dump([], f)
    
    return crashvault_dir


if __name__ == "__main__":
    create_user_config()
