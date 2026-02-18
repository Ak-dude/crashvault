"""Slack webhook provider."""

import json
import logging
import urllib.request
import urllib.error
from typing import Any, Dict, List

from .base import WebhookConfig, WebhookPayload, WebhookProvider
from .dispatcher import register_provider


logger = logging.getLogger("crashvault")


class SlackWebhook(WebhookProvider):
    """Send notifications to Slack via incoming webhooks."""

    def send(self, payload: WebhookPayload) -> bool:
        """Send a Slack notification."""
        try:
            slack_payload = self._build_slack_payload(payload)
            data = json.dumps(slack_payload).encode("utf-8")

            req = urllib.request.Request(
                self.config.url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                return response.status == 200

        except urllib.error.URLError as e:
            logger.error(f"Slack webhook failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Slack webhook error: {e}")
            return False

    def _build_slack_payload(self, payload: WebhookPayload) -> Dict[str, Any]:
        """Build a Slack Block Kit message."""
        level_emoji = {
            "debug": ":mag:",
            "info": ":information_source:",
            "warning": ":warning:",
            "error": ":x:",
            "critical": ":fire:",
        }
        emoji = level_emoji.get(payload.level.lower(), ":pushpin:")

        blocks: List[Dict[str, Any]] = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} CrashVault Alert",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Level:*\n{payload.level.upper()}"},
                    {"type": "mrkdwn", "text": f"*Issue:*\n#{payload.issue_id}"},
                ],
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Message:*\n{payload.message[:500]}",
                },
            },
        ]

        # Add host info if available
        if payload.host:
            blocks.append({
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": f"Host: `{payload.host}`"},
                ],
            })

        # Add tags if available
        if payload.tags:
            tags_str = " ".join([f"`{tag}`" for tag in payload.tags])
            blocks.append({
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": f"Tags: {tags_str}"},
                ],
            })

        # Add stacktrace if available (truncated)
        if payload.stacktrace:
            stack = payload.stacktrace[:1500]
            if len(payload.stacktrace) > 1500:
                stack += "\n..."
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"```{stack}```",
                },
            })

        # Add timestamp
        if payload.timestamp:
            blocks.append({
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": f"Event: `{payload.event_id}` | {payload.timestamp}"},
                ],
            })

        return {"blocks": blocks}


# Register the provider
register_provider("slack", SlackWebhook)
