"""Base webhook provider interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import hmac
import hashlib
import json


@dataclass
class WebhookConfig:
    """Configuration for a webhook."""
    id: str
    type: str  # "slack", "discord", "http"
    url: str
    name: Optional[str] = None
    secret: Optional[str] = None
    events: Optional[List[str]] = None  # Filter by level: ["error", "critical"]
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "url": self.url,
            "name": self.name,
            "secret": self.secret,
            "events": self.events,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WebhookConfig":
        return cls(
            id=data["id"],
            type=data["type"],
            url=data["url"],
            name=data.get("name"),
            secret=data.get("secret"),
            events=data.get("events"),
            enabled=data.get("enabled", True),
        )


@dataclass
class WebhookPayload:
    """Standardized payload for webhook delivery."""
    event_id: str
    issue_id: int
    message: str
    level: str
    stacktrace: Optional[str] = None
    timestamp: Optional[str] = None
    tags: Optional[List[str]] = None
    context: Optional[Dict[str, Any]] = None
    host: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "issue_id": self.issue_id,
            "message": self.message,
            "level": self.level,
            "stacktrace": self.stacktrace,
            "timestamp": self.timestamp,
            "tags": self.tags or [],
            "context": self.context or {},
            "host": self.host,
        }

    def sign(self, secret: str) -> str:
        """Create HMAC-SHA256 signature of the payload."""
        body = json.dumps(self.to_dict(), sort_keys=True)
        return hmac.new(
            secret.encode("utf-8"),
            body.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()


class WebhookProvider(ABC):
    """Abstract base class for webhook providers."""

    def __init__(self, config: WebhookConfig):
        self.config = config

    @abstractmethod
    def send(self, payload: WebhookPayload) -> bool:
        """
        Send a webhook notification.

        Returns True if successful, False otherwise.
        """
        pass

    def should_send(self, payload: WebhookPayload) -> bool:
        """Check if this webhook should receive this event based on filters."""
        if not self.config.enabled:
            return False

        # If no event filter, send all events
        if not self.config.events:
            return True

        # Check if event level matches filter
        return payload.level.lower() in [e.lower() for e in self.config.events]

    def format_message(self, payload: WebhookPayload) -> str:
        """Format the error message for display."""
        level_emoji = {
            "debug": "🔍",
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "critical": "🔥",
        }
        emoji = level_emoji.get(payload.level.lower(), "📌")

        msg = f"{emoji} [{payload.level.upper()}] Issue #{payload.issue_id}\n"
        msg += f"**{payload.message}**\n"

        if payload.host:
            msg += f"Host: {payload.host}\n"

        if payload.tags:
            msg += f"Tags: {', '.join(payload.tags)}\n"

        if payload.stacktrace:
            # Truncate stacktrace for readability
            stack = payload.stacktrace[:500]
            if len(payload.stacktrace) > 500:
                stack += "\n..."
            msg += f"\n```\n{stack}\n```"

        return msg
