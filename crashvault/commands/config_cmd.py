import click, json
from ..core import load_config, save_config
from ..rich_utils import get_console

console = get_console()


@click.group()
def config_group():
    """Manage Crashvault configuration."""
    pass


@config_group.command("get")
@click.argument("key")
def config_get(key):
    cfg = load_config()
    value = cfg.get(key)
    if value is not None:
        console.print(f"[highlight]{key}:[/highlight] {json.dumps(value)}")
    else:
        console.print(f"[warning]Key '{key}' not found in config[/warning]")


@config_group.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key, value):
    cfg = load_config()
    try:
        cfg[key] = json.loads(value)
    except Exception:
        cfg[key] = value
    save_config(cfg)
    console.print(f"[success]Config updated:[/success] [highlight]{key}[/highlight] = {json.dumps(cfg[key])}")


@config_group.command("colors")
def config_colors():
    """Show available color configuration options."""
    console.print("\n[highlight]Available Color Settings:[/highlight]")
    console.print("\nThese colors can be customized using:")
    console.print('  [info]crashvault config set colors \'{"key": "color"}\'[/info]\n')

    color_descriptions = {
        "success": "Successful operations (green)",
        "error": "Error messages (red)",
        "warning": "Warning messages (yellow)",
        "info": "Informational messages (cyan)",
        "primary": "Primary emphasis (blue)",
        "secondary": "Secondary text (magenta)",
        "muted": "Less important text (dim)",
        "highlight": "Important highlights (bold cyan)",
        "danger": "Critical/dangerous operations (bold red)",
    }

    for key, desc in color_descriptions.items():
        console.print(f"  [highlight]{key:12}[/highlight] - {desc}")

    console.print("\n[muted]Example:[/muted]")
    console.print('  crashvault config set colors \'{"success": "bright_green", "error": "bold red"}\'')

    cfg = load_config()
    current_colors = cfg.get("colors", {})
    if current_colors:
        console.print(f"\n[highlight]Current custom colors:[/highlight]")
        for key, value in current_colors.items():
            console.print(f"  {key}: {value}")


