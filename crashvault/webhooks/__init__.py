"""Webhook providers for CrashVault."""

from .base import WebhookProvider
from .dispatcher import WebhookDispatcher, dispatch_webhooks
from .slack import SlackWebhook
from .discord import DiscordWebhook
from .http import HTTPWebhook

__all__ = [
    "WebhookProvider",
    "WebhookDispatcher",
    "dispatch_webhooks",
    "SlackWebhook",
    "DiscordWebhook",
    "HTTPWebhook",
]
