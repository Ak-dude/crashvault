"""Generic HTTP webhook provider."""

import json
import logging
import urllib.request
import urllib.error
from typing import Any, Dict

from .base import WebhookConfig, WebhookPayload, WebhookProvider
from .dispatcher import register_provider


logger = logging.getLogger("crashvault")


class HTTPWebhook(WebhookProvider):
    """Send notifications to any HTTP endpoint."""

    def send(self, payload: WebhookPayload) -> bool:
        """Send an HTTP POST notification."""
        try:
            http_payload = self._build_http_payload(payload)
            data = json.dumps(http_payload).encode("utf-8")

            headers = {
                "Content-Type": "application/json",
                "User-Agent": "CrashVault/1.0",
                "X-CrashVault-Event": payload.event_id,
            }

            # Add signature if secret is configured
            if self.config.secret:
                signature = payload.sign(self.config.secret)
                headers["X-CrashVault-Signature"] = f"sha256={signature}"

            req = urllib.request.Request(
                self.config.url,
                data=data,
                headers=headers,
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                # Accept any 2xx status code
                return 200 <= response.status < 300

        except urllib.error.URLError as e:
            logger.error(f"HTTP webhook failed: {e}")
            return False
        except Exception as e:
            logger.error(f"HTTP webhook error: {e}")
            return False

    def _build_http_payload(self, payload: WebhookPayload) -> Dict[str, Any]:
        """Build the HTTP payload - full event data."""
        return {
            "type": "crashvault.event",
            "data": payload.to_dict(),
        }


# Register the provider
register_provider("http", HTTPWebhook)
