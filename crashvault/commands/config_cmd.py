import click, json
from ..core import load_config, save_config


@click.group()
def config_group():
    """Manage Crashvault configuration."""
    pass


@config_group.command("get")
@click.argument("key")
def config_get(key):
    cfg = load_config()
    click.echo(json.dumps(cfg.get(key)))


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
    click.echo("ok")


