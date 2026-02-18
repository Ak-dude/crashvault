"""Webhook management commands."""

import click

from ..webhooks.dispatcher import get_dispatcher


@click.group(name="webhook")
def webhook():
    """Manage outbound webhooks for notifications."""
    pass


@webhook.command(name="add")
@click.argument("type", type=click.Choice(["slack", "discord", "http"]))
@click.option("--url", required=True, help="Webhook URL")
@click.option("--name", default=None, help="Friendly name for this webhook")
@click.option("--secret", default=None, help="Secret for signing payloads (HTTP only)")
@click.option("--events", default=None, help="Comma-separated event levels to filter (e.g., 'error,critical')")
def add(type, url, name, secret, events):
    """Add a new webhook.

    TYPE is one of: slack, discord, http

    Examples:
        crashvault webhook add slack --url=https://hooks.slack.com/services/xxx
        crashvault webhook add discord --url=https://discord.com/api/webhooks/xxx
        crashvault webhook add http --url=https://myapp.com/webhook --secret=mysecret
    """
    # Import providers to register them
    from .. import webhooks  # noqa

    event_list = None
    if events:
        event_list = [e.strip().lower() for e in events.split(",")]

    dispatcher = get_dispatcher()
    webhook = dispatcher.add_webhook(
        type=type,
        url=url,
        name=name,
        secret=secret,
        events=event_list,
    )

    click.echo(f"Webhook added: {webhook.id}")
    click.echo(f"  Type: {webhook.type}")
    click.echo(f"  Name: {webhook.name}")
    if event_list:
        click.echo(f"  Events: {', '.join(event_list)}")
    else:
        click.echo("  Events: all")


@webhook.command(name="list")
def list_webhooks():
    """List all configured webhooks."""
    dispatcher = get_dispatcher()
    webhooks = dispatcher.list_webhooks()

    if not webhooks:
        click.echo("No webhooks configured.")
        click.echo("Add one with: crashvault webhook add <type> --url=<url>")
        return

    click.echo(f"{'ID':<10} {'Type':<10} {'Name':<20} {'Enabled':<8} {'Events'}")
    click.echo("-" * 70)

    for w in webhooks:
        events = ", ".join(w.events) if w.events else "all"
        enabled = "✓" if w.enabled else "✗"
        click.echo(f"{w.id:<10} {w.type:<10} {(w.name or '-'):<20} {enabled:<8} {events}")


@webhook.command(name="remove")
@click.argument("webhook_id")
def remove(webhook_id):
    """Remove a webhook by ID."""
    dispatcher = get_dispatcher()

    if dispatcher.remove_webhook(webhook_id):
        click.echo(f"Webhook {webhook_id} removed.")
    else:
        click.echo(f"Webhook {webhook_id} not found.", err=True)


@webhook.command(name="test")
@click.argument("webhook_id")
def test(webhook_id):
    """Send a test notification to a webhook."""
    # Import providers to register them
    from .. import webhooks  # noqa

    dispatcher = get_dispatcher()
    webhook = dispatcher.get_webhook(webhook_id)

    if not webhook:
        click.echo(f"Webhook {webhook_id} not found.", err=True)
        return

    click.echo(f"Sending test to {webhook.type} webhook...")

    if dispatcher.test_webhook(webhook_id):
        click.echo("✓ Test notification sent successfully!")
    else:
        click.echo("✗ Test notification failed. Check the webhook URL.", err=True)


@webhook.command(name="enable")
@click.argument("webhook_id")
def enable(webhook_id):
    """Enable a webhook."""
    dispatcher = get_dispatcher()

    if dispatcher.toggle_webhook(webhook_id, True):
        click.echo(f"Webhook {webhook_id} enabled.")
    else:
        click.echo(f"Webhook {webhook_id} not found.", err=True)


@webhook.command(name="disable")
@click.argument("webhook_id")
def disable(webhook_id):
    """Disable a webhook."""
    dispatcher = get_dispatcher()

    if dispatcher.toggle_webhook(webhook_id, False):
        click.echo(f"Webhook {webhook_id} disabled.")
    else:
        click.echo(f"Webhook {webhook_id} not found.", err=True)


@webhook.command(name="show")
@click.argument("webhook_id")
def show(webhook_id):
    """Show details for a specific webhook."""
    dispatcher = get_dispatcher()
    w = dispatcher.get_webhook(webhook_id)

    if not w:
        click.echo(f"Webhook {webhook_id} not found.", err=True)
        return

    click.echo(f"ID:      {w.id}")
    click.echo(f"Type:    {w.type}")
    click.echo(f"Name:    {w.name or '-'}")
    click.echo(f"URL:     {w.url}")
    click.echo(f"Enabled: {'Yes' if w.enabled else 'No'}")
    click.echo(f"Events:  {', '.join(w.events) if w.events else 'all'}")
    if w.secret:
        click.echo(f"Secret:  {'*' * 8} (configured)")
