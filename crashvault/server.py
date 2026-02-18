"""HTTP server for receiving runtime errors from external applications."""

import hashlib
import json
import logging
import os
import platform
import signal
import sys
import uuid
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlparse

from .core import (
    ensure_dirs,
    load_issues,
    save_issues,
    event_path_for,
    load_config,
    save_config,
    ROOT,
)
from .webhooks.dispatcher import dispatch_webhooks


logger = logging.getLogger("crashvault")

DEFAULT_PORT = 5678
PID_FILE = ROOT / "server.pid"


class CrashVaultHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the CrashVault server."""

    def log_message(self, format, *args):
        """Override to use our logger."""
        logger.info(f"HTTP {args[0]}")

    def send_json_response(self, status: int, data: Dict[str, Any]):
        """Send a JSON response."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-API-Key")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-API-Key")
        self.end_headers()

    def do_GET(self):
        """Handle GET requests."""
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/health" or path == "/health":
            self.send_json_response(200, {
                "status": "ok",
                "service": "crashvault",
                "version": "1.0.0",
            })
        elif path == "/api/v1/stats":
            self._handle_stats()
        else:
            self.send_json_response(404, {"error": "Not found"})

    def do_POST(self):
        """Handle POST requests."""
        parsed = urlparse(self.path)
        path = parsed.path

        # Read request body
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length > 1024 * 1024:  # 1MB limit
            self.send_json_response(413, {"error": "Payload too large"})
            return

        try:
            body = self.rfile.read(content_length)
            data = json.loads(body.decode("utf-8")) if body else {}
        except json.JSONDecodeError:
            self.send_json_response(400, {"error": "Invalid JSON"})
            return

        if path in ("/api/v1/events", "/api/v1/errors", "/api/events"):
            self._handle_event(data)
        elif path == "/api/v1/batch":
            self._handle_batch(data)
        else:
            self.send_json_response(404, {"error": "Not found"})

    def _handle_event(self, data: Dict[str, Any]):
        """Handle a single error event."""
        # Validate required fields
        message = data.get("message")
        if not message:
            self.send_json_response(400, {"error": "message is required"})
            return

        # Extract optional fields
        stacktrace = data.get("stacktrace", data.get("stack", ""))
        level = data.get("level", "error").lower()
        if level not in ("debug", "info", "warning", "error", "critical"):
            level = "error"

        tags = data.get("tags", [])
        if isinstance(tags, str):
            tags = [tags]

        context = data.get("context", {})
        if not isinstance(context, dict):
            context = {}

        # Add source info if provided
        source = data.get("source", data.get("url", ""))
        if source:
            context["source"] = source

        line = data.get("line", data.get("lineno"))
        if line:
            context["line"] = line

        column = data.get("column", data.get("colno"))
        if column:
            context["column"] = column

        # Create fingerprint from message
        fp = hashlib.sha1(message.encode("utf-8")).hexdigest()[:8]

        # Load/create issue
        ensure_dirs()
        issues = load_issues()
        issue = next((i for i in issues if i["fingerprint"] == fp), None)
        created_new = False

        if not issue:
            issue = {
                "id": len(issues) + 1,
                "fingerprint": fp,
                "title": message[:80],
                "status": "open",
                "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            }
            issues.append(issue)
            save_issues(issues)
            created_new = True

        # Create event
        event_id = str(uuid.uuid4())
        ts = datetime.now(timezone.utc)
        event_data = {
            "event_id": event_id,
            "issue_id": issue["id"],
            "message": message,
            "stacktrace": stacktrace,
            "timestamp": ts.isoformat().replace("+00:00", "Z"),
            "level": level,
            "tags": tags,
            "context": context,
            "host": data.get("host", self.client_address[0]),
            "pid": data.get("pid", 0),
        }

        # Save event
        path = event_path_for(event_id, ts)
        tmp = path.with_suffix(path.suffix + ".tmp")
        with open(tmp, "w") as f:
            json.dump(event_data, f, indent=2)
        os.replace(tmp, path)

        logger.info(f"event received | issue_id={issue['id']} | event_id={event_id} | level={level}")

        # Dispatch webhooks
        dispatch_webhooks(event_data)

        self.send_json_response(201, {
            "success": True,
            "event_id": event_id,
            "issue_id": issue["id"],
            "issue_created": created_new,
        })

    def _handle_batch(self, data: Dict[str, Any]):
        """Handle a batch of events."""
        events = data.get("events", [])
        if not isinstance(events, list):
            self.send_json_response(400, {"error": "events must be an array"})
            return

        if len(events) > 100:
            self.send_json_response(400, {"error": "Maximum 100 events per batch"})
            return

        results = []
        for event_data in events:
            if isinstance(event_data, dict) and event_data.get("message"):
                # Reuse single event handler logic (simplified)
                message = event_data["message"]
                fp = hashlib.sha1(message.encode("utf-8")).hexdigest()[:8]

                ensure_dirs()
                issues = load_issues()
                issue = next((i for i in issues if i["fingerprint"] == fp), None)

                if not issue:
                    issue = {
                        "id": len(issues) + 1,
                        "fingerprint": fp,
                        "title": message[:80],
                        "status": "open",
                        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    }
                    issues.append(issue)
                    save_issues(issues)

                event_id = str(uuid.uuid4())
                ts = datetime.now(timezone.utc)
                ev = {
                    "event_id": event_id,
                    "issue_id": issue["id"],
                    "message": message,
                    "stacktrace": event_data.get("stacktrace", ""),
                    "timestamp": ts.isoformat().replace("+00:00", "Z"),
                    "level": event_data.get("level", "error"),
                    "tags": event_data.get("tags", []),
                    "context": event_data.get("context", {}),
                    "host": event_data.get("host", self.client_address[0]),
                    "pid": event_data.get("pid", 0),
                }

                path = event_path_for(event_id, ts)
                tmp = path.with_suffix(path.suffix + ".tmp")
                with open(tmp, "w") as f:
                    json.dump(ev, f, indent=2)
                os.replace(tmp, path)

                dispatch_webhooks(ev)
                results.append({"event_id": event_id, "issue_id": issue["id"]})

        self.send_json_response(201, {
            "success": True,
            "processed": len(results),
            "results": results,
        })

    def _handle_stats(self):
        """Return basic stats."""
        from .core import load_events

        events = load_events()
        issues = load_issues()

        level_counts = {}
        for ev in events:
            level = ev.get("level", "unknown")
            level_counts[level] = level_counts.get(level, 0) + 1

        self.send_json_response(200, {
            "total_issues": len(issues),
            "total_events": len(events),
            "events_by_level": level_counts,
            "open_issues": len([i for i in issues if i.get("status") == "open"]),
        })


def run_server(port: int = DEFAULT_PORT, host: str = "0.0.0.0"):
    """Start the CrashVault HTTP server."""
    from .core import configure_logging
    ensure_dirs()
    configure_logging()

    # Import webhook providers to register them
    from . import webhooks  # noqa

    server = HTTPServer((host, port), CrashVaultHandler)

    # Save PID for stop command
    PID_FILE.write_text(str(os.getpid()))

    def cleanup(signum, frame):
        logger.info("Server shutting down...")
        if PID_FILE.exists():
            PID_FILE.unlink()
        server.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGINT, cleanup)

    logger.info(f"CrashVault server starting on {host}:{port}")
    print(f"CrashVault server listening on http://{host}:{port}")
    print(f"  POST /api/v1/events  - Submit error events")
    print(f"  GET  /api/health     - Health check")
    print(f"  GET  /api/v1/stats   - Get statistics")
    print(f"\nPress Ctrl+C to stop")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        cleanup(None, None)


def stop_server():
    """Stop the running CrashVault server."""
    if not PID_FILE.exists():
        return False, "No server running"

    try:
        pid = int(PID_FILE.read_text().strip())
        os.kill(pid, signal.SIGTERM)
        PID_FILE.unlink()
        return True, f"Server (PID {pid}) stopped"
    except ProcessLookupError:
        PID_FILE.unlink()
        return False, "Server was not running (stale PID file removed)"
    except Exception as e:
        return False, str(e)


def is_server_running() -> Optional[int]:
    """Check if server is running, return PID if so."""
    if not PID_FILE.exists():
        return None

    try:
        pid = int(PID_FILE.read_text().strip())
        os.kill(pid, 0)  # Check if process exists
        return pid
    except (ProcessLookupError, ValueError):
        return None
