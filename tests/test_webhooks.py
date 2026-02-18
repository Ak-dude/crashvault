"""
Tests for the webhook subsystem.
"""
import json
import hmac
import hashlib
from unittest.mock import patch, MagicMock


class TestWebhookConfig:
    """Tests for WebhookConfig dataclass."""

    def test_to_dict(self):
        """to_dict should return all fields as a dictionary."""
        from crashvault.webhooks.base import WebhookConfig

        config = WebhookConfig(
            id="test-123",
            type="slack",
            url="https://hooks.slack.com/test",
            name="Test Webhook",
            secret="secret123",
            events=["error", "critical"],
            enabled=True,
        )

        result = config.to_dict()

        assert result["id"] == "test-123"
        assert result["type"] == "slack"
        assert result["url"] == "https://hooks.slack.com/test"
        assert result["name"] == "Test Webhook"
        assert result["secret"] == "secret123"
        assert result["events"] == ["error", "critical"]
        assert result["enabled"] is True

    def test_from_dict(self):
        """from_dict should create WebhookConfig from dictionary."""
        from crashvault.webhooks.base import WebhookConfig

        data = {
            "id": "test-456",
            "type": "discord",
            "url": "https://discord.com/webhook",
            "name": "Discord Hook",
            "secret": None,
            "events": ["warning"],
            "enabled": False,
        }

        config = WebhookConfig.from_dict(data)

        assert config.id == "test-456"
        assert config.type == "discord"
        assert config.enabled is False
        assert config.events == ["warning"]

    def test_from_dict_defaults(self):
        """from_dict should use defaults for optional fields."""
        from crashvault.webhooks.base import WebhookConfig

        data = {
            "id": "minimal",
            "type": "http",
            "url": "https://example.com/webhook",
        }

        config = WebhookConfig.from_dict(data)

        assert config.name is None
        assert config.secret is None
        assert config.events is None
        assert config.enabled is True  # Default

    def test_roundtrip(self):
        """to_dict -> from_dict should preserve all data."""
        from crashvault.webhooks.base import WebhookConfig

        original = WebhookConfig(
            id="round-trip",
            type="slack",
            url="https://hooks.slack.com/test",
            name="Roundtrip Test",
            secret="secret",
            events=["error"],
            enabled=True,
        )

        result = WebhookConfig.from_dict(original.to_dict())

        assert result.id == original.id
        assert result.type == original.type
        assert result.url == original.url
        assert result.name == original.name
        assert result.secret == original.secret
        assert result.events == original.events
        assert result.enabled == original.enabled


class TestWebhookPayload:
    """Tests for WebhookPayload dataclass."""

    def test_to_dict(self):
        """to_dict should return all fields."""
        from crashvault.webhooks.base import WebhookPayload

        payload = WebhookPayload(
            event_id="evt-123",
            issue_id=42,
            message="Test error",
            level="error",
            stacktrace="File test.py line 1",
            timestamp="2024-01-01T00:00:00Z",
            tags=["backend"],
            context={"user_id": "123"},
            host="testhost",
        )

        result = payload.to_dict()

        assert result["event_id"] == "evt-123"
        assert result["issue_id"] == 42
        assert result["message"] == "Test error"
        assert result["level"] == "error"
        assert result["tags"] == ["backend"]
        assert result["context"] == {"user_id": "123"}

    def test_to_dict_defaults(self):
        """to_dict should use empty defaults for None values."""
        from crashvault.webhooks.base import WebhookPayload

        payload = WebhookPayload(
            event_id="evt-456",
            issue_id=1,
            message="Minimal",
            level="info",
        )

        result = payload.to_dict()

        assert result["tags"] == []
        assert result["context"] == {}

    def test_sign(self):
        """sign should return consistent HMAC-SHA256 digest."""
        from crashvault.webhooks.base import WebhookPayload

        payload = WebhookPayload(
            event_id="sign-test",
            issue_id=1,
            message="Test message",
            level="error",
        )

        secret = "my-secret-key"
        signature = payload.sign(secret)

        # Verify it's a valid hex string
        assert len(signature) == 64  # SHA256 hex = 64 chars
        int(signature, 16)  # Should be valid hex

        # Verify it's consistent
        assert payload.sign(secret) == signature

        # Verify different secret produces different signature
        assert payload.sign("different-secret") != signature

    def test_sign_matches_manual_hmac(self):
        """sign should match manual HMAC calculation."""
        from crashvault.webhooks.base import WebhookPayload

        payload = WebhookPayload(
            event_id="hmac-test",
            issue_id=5,
            message="HMAC test",
            level="warning",
        )

        secret = "test-secret"
        signature = payload.sign(secret)

        # Manual calculation
        body = json.dumps(payload.to_dict(), sort_keys=True)
        expected = hmac.new(
            secret.encode("utf-8"),
            body.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        assert signature == expected


class TestWebhookProvider:
    """Tests for WebhookProvider base class."""

    def test_should_send_when_disabled(self):
        """should_send returns False when webhook is disabled."""
        from crashvault.webhooks.base import WebhookConfig, WebhookPayload, WebhookProvider

        class TestProvider(WebhookProvider):
            def send(self, payload):
                return True

        config = WebhookConfig(
            id="disabled",
            type="test",
            url="https://example.com",
            enabled=False,
        )
        provider = TestProvider(config)

        payload = WebhookPayload(
            event_id="test",
            issue_id=1,
            message="Test",
            level="error",
        )

        assert provider.should_send(payload) is False

    def test_should_send_all_when_no_filter(self):
        """should_send returns True for all levels when no filter set."""
        from crashvault.webhooks.base import WebhookConfig, WebhookPayload, WebhookProvider

        class TestProvider(WebhookProvider):
            def send(self, payload):
                return True

        config = WebhookConfig(
            id="unfiltered",
            type="test",
            url="https://example.com",
            events=None,
            enabled=True,
        )
        provider = TestProvider(config)

        for level in ["debug", "info", "warning", "error", "critical"]:
            payload = WebhookPayload(
                event_id="test",
                issue_id=1,
                message="Test",
                level=level,
            )
            assert provider.should_send(payload) is True

    def test_should_send_respects_level_filter(self):
        """should_send respects the events level filter."""
        from crashvault.webhooks.base import WebhookConfig, WebhookPayload, WebhookProvider

        class TestProvider(WebhookProvider):
            def send(self, payload):
                return True

        config = WebhookConfig(
            id="filtered",
            type="test",
            url="https://example.com",
            events=["error", "critical"],
            enabled=True,
        )
        provider = TestProvider(config)

        # Should match
        for level in ["error", "critical", "ERROR", "CRITICAL"]:
            payload = WebhookPayload(
                event_id="test",
                issue_id=1,
                message="Test",
                level=level,
            )
            assert provider.should_send(payload) is True

        # Should not match
        for level in ["debug", "info", "warning"]:
            payload = WebhookPayload(
                event_id="test",
                issue_id=1,
                message="Test",
                level=level,
            )
            assert provider.should_send(payload) is False


class TestWebhookDispatcher:
    """Tests for WebhookDispatcher class."""

    def test_add_webhook(self, crashvault_home):
        """add_webhook should create and persist a webhook."""
        from crashvault.webhooks.dispatcher import WebhookDispatcher
        from crashvault.core import load_config

        dispatcher = WebhookDispatcher()
        webhook = dispatcher.add_webhook(
            type="slack",
            url="https://hooks.slack.com/test",
            name="Test Hook",
        )

        assert webhook.type == "slack"
        assert webhook.url == "https://hooks.slack.com/test"
        assert webhook.name == "Test Hook"
        assert webhook.enabled is True

        # Check persisted
        config = load_config()
        assert len(config["webhooks"]) == 1
        assert config["webhooks"][0]["type"] == "slack"

    def test_remove_webhook(self, crashvault_home):
        """remove_webhook should delete webhook and persist."""
        from crashvault.webhooks.dispatcher import WebhookDispatcher
        from crashvault.core import load_config

        dispatcher = WebhookDispatcher()
        webhook = dispatcher.add_webhook(type="slack", url="https://test.com")
        webhook_id = webhook.id

        result = dispatcher.remove_webhook(webhook_id)

        assert result is True
        assert dispatcher.get_webhook(webhook_id) is None

        config = load_config()
        assert len(config.get("webhooks", [])) == 0

    def test_remove_nonexistent_webhook(self, crashvault_home):
        """remove_webhook returns False for nonexistent webhook."""
        from crashvault.webhooks.dispatcher import WebhookDispatcher

        dispatcher = WebhookDispatcher()
        result = dispatcher.remove_webhook("nonexistent")

        assert result is False

    def test_get_webhook(self, crashvault_home):
        """get_webhook should return webhook by ID."""
        from crashvault.webhooks.dispatcher import WebhookDispatcher

        dispatcher = WebhookDispatcher()
        webhook = dispatcher.add_webhook(type="discord", url="https://discord.com/webhook")

        result = dispatcher.get_webhook(webhook.id)

        assert result is not None
        assert result.id == webhook.id
        assert result.type == "discord"

    def test_get_nonexistent_webhook(self, crashvault_home):
        """get_webhook returns None for nonexistent ID."""
        from crashvault.webhooks.dispatcher import WebhookDispatcher

        dispatcher = WebhookDispatcher()
        result = dispatcher.get_webhook("nonexistent")

        assert result is None

    def test_list_webhooks(self, crashvault_home):
        """list_webhooks should return all webhooks."""
        from crashvault.webhooks.dispatcher import WebhookDispatcher

        dispatcher = WebhookDispatcher()
        dispatcher.add_webhook(type="slack", url="https://slack.com")
        dispatcher.add_webhook(type="discord", url="https://discord.com")

        webhooks = dispatcher.list_webhooks()

        assert len(webhooks) == 2
        types = {w.type for w in webhooks}
        assert types == {"slack", "discord"}

    def test_toggle_webhook(self, crashvault_home):
        """toggle_webhook should enable/disable webhook."""
        from crashvault.webhooks.dispatcher import WebhookDispatcher
        from crashvault.core import load_config

        dispatcher = WebhookDispatcher()
        webhook = dispatcher.add_webhook(type="http", url="https://example.com")

        # Disable
        result = dispatcher.toggle_webhook(webhook.id, enabled=False)
        assert result is True
        assert dispatcher.get_webhook(webhook.id).enabled is False

        # Enable
        result = dispatcher.toggle_webhook(webhook.id, enabled=True)
        assert result is True
        assert dispatcher.get_webhook(webhook.id).enabled is True

        # Check persisted
        config = load_config()
        assert config["webhooks"][0]["enabled"] is True

    def test_toggle_nonexistent_webhook(self, crashvault_home):
        """toggle_webhook returns False for nonexistent webhook."""
        from crashvault.webhooks.dispatcher import WebhookDispatcher

        dispatcher = WebhookDispatcher()
        result = dispatcher.toggle_webhook("nonexistent", enabled=True)

        assert result is False


class TestDispatchWebhooks:
    """Tests for the dispatch_webhooks function."""

    def test_dispatch_webhooks_builds_payload(self, crashvault_home):
        """dispatch_webhooks should build WebhookPayload from event data."""
        from crashvault.webhooks.dispatcher import dispatch_webhooks, get_dispatcher, _dispatcher
        from crashvault.webhooks.base import WebhookPayload

        # Reset global dispatcher
        import crashvault.webhooks.dispatcher as dispatcher_module
        dispatcher_module._dispatcher = None

        event_data = {
            "event_id": "evt-test",
            "issue_id": 42,
            "message": "Test error message",
            "level": "error",
            "stacktrace": "traceback here",
            "timestamp": "2024-01-01T00:00:00Z",
            "tags": ["api", "backend"],
            "context": {"user_id": "123"},
            "host": "testhost",
        }

        # With no webhooks configured, dispatch should return empty dict
        result = dispatch_webhooks(event_data)
        assert result == {}

    def test_dispatch_calls_providers(self, crashvault_home):
        """dispatch should call send on matching providers."""
        from crashvault.webhooks.dispatcher import WebhookDispatcher, register_provider
        from crashvault.webhooks.base import WebhookConfig, WebhookPayload, WebhookProvider

        # Create a mock provider
        class MockProvider(WebhookProvider):
            calls = []

            def send(self, payload):
                MockProvider.calls.append(payload)
                return True

        register_provider("mock", MockProvider)
        MockProvider.calls = []

        dispatcher = WebhookDispatcher()
        dispatcher.add_webhook(type="mock", url="https://mock.com")

        payload = WebhookPayload(
            event_id="test",
            issue_id=1,
            message="Test",
            level="error",
        )

        results = dispatcher.dispatch(payload)

        assert len(MockProvider.calls) == 1
        assert MockProvider.calls[0].event_id == "test"
