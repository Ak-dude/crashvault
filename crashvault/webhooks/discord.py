"""Discord webhook provider."""

import json
import logging
import urllib.request
import urllib.error
from typing import Any, Dict, List

from .base import WebhookConfig, WebhookPayload, WebhookProvider
from .dispatcher import register_provider


logger = logging.getLogger("crashvault")


class DiscordWebhook(WebhookProvider):
    """Send notifications to Discord via webhooks."""

    def send(self, payload: WebhookPayload) -> bool:
        """Send a Discord notification."""
        try:
            discord_payload = self._build_discord_payload(payload)
            data = json.dumps(discord_payload).encode("utf-8")

            req = urllib.request.Request(
                self.config.url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                # Discord returns 204 No Content on success
                return response.status in (200, 204)

        except urllib.error.URLError as e:
            logger.error(f"Discord webhook failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Discord webhook error: {e}")
            return False

    def _build_discord_payload(self, payload: WebhookPayload) -> Dict[str, Any]:
        """Build a Discord embed message."""
        # Color based on level
        level_colors = {
            "debug": 0x6B7280,   # Gray
            "info": 0x3B82F6,    # Blue
            "warning": 0xF59E0B, # Amber
            "error": 0xEF4444,   # Red
            "critical": 0x7C2D12, # Dark red
        }
        color = level_colors.get(payload.level.lower(), 0x6B7280)

        level_emoji = {
            "debug": "🔍",
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "critical": "🔥",
        }
        emoji = level_emoji.get(payload.level.lower(), "📌")

        fields: List[Dict[str, Any]] = [
            {
                "name": "Level",
                "value": f"{emoji} {payload.level.upper()}",
                "inline": True,
            },
            {
                "name": "Issue",
                "value": f"#{payload.issue_id}",
                "inline": True,
            },
        ]

        if payload.host:
            fields.append({
                "name": "Host",
                "value": f"`{payload.host}`",
                "inline": True,
            })

        if payload.tags:
            fields.append({
                "name": "Tags",
                "value": ", ".join([f"`{tag}`" for tag in payload.tags]),
                "inline": False,
            })

        embed: Dict[str, Any] = {
            "title": "CrashVault Alert",
            "description": payload.message[:2000],
            "color": color,
            "fields": fields,
        }

        # Add stacktrace if available
        if payload.stacktrace:
            stack = payload.stacktrace[:1000]
            if len(payload.stacktrace) > 1000:
                stack += "\n..."
            embed["fields"].append({
                "name": "Stacktrace",
                "value": f"```\n{stack}\n```",
                "inline": False,
            })

        # Add footer with event info
        if payload.timestamp:
            embed["footer"] = {
                "text": f"Event: {payload.event_id}",
            }
            embed["timestamp"] = payload.timestamp

        return {
            "username": "CrashVault",
            "embeds": [embed],
        }


# Register the provider
register_provider("discord", DiscordWebhook)
