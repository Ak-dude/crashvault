"""Webhook dispatcher - manages and sends webhooks."""

import logging
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Type

from ..core import load_config, save_config
from .base import WebhookConfig, WebhookPayload, WebhookProvider


logger = logging.getLogger("crashvault")

# Registry of webhook provider types
_PROVIDERS: Dict[str, Type[WebhookProvider]] = {}


def register_provider(type_name: str, provider_class: Type[WebhookProvider]):
    """Register a webhook provider type."""
    _PROVIDERS[type_name] = provider_class


def get_provider(config: WebhookConfig) -> Optional[WebhookProvider]:
    """Get a webhook provider instance for the given config."""
    provider_class = _PROVIDERS.get(config.type)
    if provider_class:
        return provider_class(config)
    return None


class WebhookDispatcher:
    """Manages webhook configurations and dispatches events."""

    def __init__(self):
        self.webhooks: List[WebhookConfig] = []
        self._load_webhooks()

    def _load_webhooks(self):
        """Load webhooks from config."""
        config = load_config()
        webhook_data = config.get("webhooks", [])
        self.webhooks = [WebhookConfig.from_dict(w) for w in webhook_data]

    def _save_webhooks(self):
        """Save webhooks to config."""
        config = load_config()
        config["webhooks"] = [w.to_dict() for w in self.webhooks]
        save_config(config)

    def add_webhook(
        self,
        type: str,
        url: str,
        name: Optional[str] = None,
        secret: Optional[str] = None,
        events: Optional[List[str]] = None,
    ) -> WebhookConfig:
        """Add a new webhook configuration."""
        webhook = WebhookConfig(
            id=str(uuid.uuid4())[:8],
            type=type,
            url=url,
            name=name or f"{type}-webhook",
            secret=secret,
            events=events,
            enabled=True,
        )
        self.webhooks.append(webhook)
        self._save_webhooks()
        logger.info(f"webhook added | id={webhook.id} | type={type}")
        return webhook

    def remove_webhook(self, webhook_id: str) -> bool:
        """Remove a webhook by ID."""
        for i, w in enumerate(self.webhooks):
            if w.id == webhook_id:
                del self.webhooks[i]
                self._save_webhooks()
                logger.info(f"webhook removed | id={webhook_id}")
                return True
        return False

    def get_webhook(self, webhook_id: str) -> Optional[WebhookConfig]:
        """Get a webhook by ID."""
        for w in self.webhooks:
            if w.id == webhook_id:
                return w
        return None

    def list_webhooks(self) -> List[WebhookConfig]:
        """List all configured webhooks."""
        return self.webhooks

    def toggle_webhook(self, webhook_id: str, enabled: bool) -> bool:
        """Enable or disable a webhook."""
        for w in self.webhooks:
            if w.id == webhook_id:
                w.enabled = enabled
                self._save_webhooks()
                return True
        return False

    def dispatch(self, payload: WebhookPayload) -> Dict[str, bool]:
        """
        Dispatch a payload to all matching webhooks.

        Returns a dict of webhook_id -> success status.
        """
        results = {}

        # Get providers for all enabled webhooks that match the event
        providers = []
        for webhook in self.webhooks:
            provider = get_provider(webhook)
            if provider and provider.should_send(payload):
                providers.append((webhook.id, provider))

        if not providers:
            return results

        # Dispatch in parallel with thread pool
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(provider.send, payload): webhook_id
                for webhook_id, provider in providers
            }

            for future in as_completed(futures):
                webhook_id = futures[future]
                try:
                    success = future.result()
                    results[webhook_id] = success
                    if success:
                        logger.info(f"webhook sent | id={webhook_id}")
                    else:
                        logger.warning(f"webhook failed | id={webhook_id}")
                except Exception as e:
                    results[webhook_id] = False
                    logger.error(f"webhook error | id={webhook_id} | error={e}")

        return results

    def test_webhook(self, webhook_id: str) -> bool:
        """Send a test event to a specific webhook."""
        webhook = self.get_webhook(webhook_id)
        if not webhook:
            return False

        provider = get_provider(webhook)
        if not provider:
            return False

        test_payload = WebhookPayload(
            event_id="test-" + str(uuid.uuid4())[:8],
            issue_id=0,
            message="This is a test notification from CrashVault",
            level="info",
            timestamp="2024-01-01T00:00:00Z",
            tags=["test"],
            host="crashvault-test",
        )

        return provider.send(test_payload)


# Global dispatcher instance
_dispatcher: Optional[WebhookDispatcher] = None


def get_dispatcher() -> WebhookDispatcher:
    """Get the global webhook dispatcher."""
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = WebhookDispatcher()
    return _dispatcher


def dispatch_webhooks(event_data: dict):
    """
    Dispatch webhooks for an event.

    This is the main entry point for triggering webhooks when an event is created.
    """
    payload = WebhookPayload(
        event_id=event_data.get("event_id", ""),
        issue_id=event_data.get("issue_id", 0),
        message=event_data.get("message", ""),
        level=event_data.get("level", "error"),
        stacktrace=event_data.get("stacktrace"),
        timestamp=event_data.get("timestamp"),
        tags=event_data.get("tags"),
        context=event_data.get("context"),
        host=event_data.get("host"),
    )

    dispatcher = get_dispatcher()
    return dispatcher.dispatch(payload)
