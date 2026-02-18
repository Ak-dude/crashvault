"""
Pytest configuration and fixtures for crashvault tests.
Cross-platform compatible (Windows, Linux, macOS).
"""
import os
import sys
import platform
import pytest
from pathlib import Path


# Platform detection helpers - can be imported by tests
IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"
IS_MACOS = platform.system() == "Darwin"
IS_UNIX = IS_LINUX or IS_MACOS


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "windows: mark test to run only on Windows")
    config.addinivalue_line("markers", "linux: mark test to run only on Linux")
    config.addinivalue_line("markers", "macos: mark test to run only on macOS")
    config.addinivalue_line("markers", "unix: mark test to run only on Unix-like systems (Linux/macOS)")


def pytest_collection_modifyitems(config, items):
    """Skip tests based on platform markers."""
    for item in items:
        # Skip Windows-only tests on non-Windows
        if "windows" in item.keywords and not IS_WINDOWS:
            item.add_marker(pytest.mark.skip(reason="Windows-only test"))

        # Skip Linux-only tests on non-Linux
        if "linux" in item.keywords and not IS_LINUX:
            item.add_marker(pytest.mark.skip(reason="Linux-only test"))

        # Skip macOS-only tests on non-macOS
        if "macos" in item.keywords and not IS_MACOS:
            item.add_marker(pytest.mark.skip(reason="macOS-only test"))

        # Skip Unix-only tests on Windows
        if "unix" in item.keywords and IS_WINDOWS:
            item.add_marker(pytest.mark.skip(reason="Unix-only test"))


@pytest.fixture
def crashvault_home(tmp_path, monkeypatch):
    """
    Creates an isolated crashvault home directory for testing.
    Sets the CRASHVAULT_HOME environment variable and reloads core module.
    """
    crashvault_dir = tmp_path / ".crashvault"
    crashvault_dir.mkdir()

    # Set the environment variable before importing core
    monkeypatch.setenv("CRASHVAULT_HOME", str(crashvault_dir))

    # We need to reload the core module to pick up the new environment variable
    # First, clear any cached imports
    modules_to_remove = [k for k in sys.modules.keys() if k.startswith('crashvault')]
    for mod in modules_to_remove:
        del sys.modules[mod]

    # Now import and setup
    from crashvault import core

    # Monkey-patch the ROOT and related paths
    monkeypatch.setattr(core, 'ROOT', crashvault_dir)
    monkeypatch.setattr(core, 'ISSUES_FILE', crashvault_dir / "issues.json")
    monkeypatch.setattr(core, 'EVENTS_DIR', crashvault_dir / "events")
    monkeypatch.setattr(core, 'LOGS_DIR', crashvault_dir / "logs")
    monkeypatch.setattr(core, 'CONFIG_FILE', crashvault_dir / "config.json")
    monkeypatch.setattr(core, 'ATTACH_DIR', crashvault_dir / "attachments")

    # Ensure dirs are created
    core.ensure_dirs()

    return crashvault_dir


@pytest.fixture
def cli_runner():
    """
    Provides a Click CLI test runner.
    """
    from click.testing import CliRunner
    return CliRunner()


@pytest.fixture
def sample_issues(crashvault_home):
    """
    Creates sample issues in the test crashvault home.
    """
    import json
    from crashvault.core import ISSUES_FILE

    issues = [
        {
            "id": 1,
            "fingerprint": "abc12345",
            "title": "Test error message",
            "status": "open",
            "created_at": "2024-01-01T00:00:00Z"
        },
        {
            "id": 2,
            "fingerprint": "def67890",
            "title": "Another test error",
            "status": "resolved",
            "created_at": "2024-01-02T00:00:00Z"
        },
        {
            "id": 3,
            "fingerprint": "ghi11111",
            "title": "Ignored issue",
            "status": "ignored",
            "created_at": "2024-01-03T00:00:00Z"
        }
    ]

    with open(ISSUES_FILE, "w") as f:
        json.dump(issues, f, indent=2)

    return issues


@pytest.fixture
def sample_events(crashvault_home, sample_issues):
    """
    Creates sample events for the sample issues.
    """
    import json
    from datetime import datetime, timezone
    from crashvault.core import EVENTS_DIR

    events = [
        {
            "event_id": "event-001",
            "issue_id": 1,
            "message": "Test error message",
            "stacktrace": "File \"test.py\", line 10\n    raise Exception()",
            "timestamp": "2024-01-01T00:00:00Z",
            "level": "error",
            "tags": ["backend", "api"],
            "context": {"user_id": "123"},
            "host": "testhost",
            "pid": 12345,
        },
        {
            "event_id": "event-002",
            "issue_id": 1,
            "message": "Test error message",
            "stacktrace": "",
            "timestamp": "2024-01-01T01:00:00Z",
            "level": "error",
            "tags": ["backend"],
            "context": {},
            "host": "testhost",
            "pid": 12346,
        },
        {
            "event_id": "event-003",
            "issue_id": 2,
            "message": "Another test error",
            "stacktrace": "",
            "timestamp": "2024-01-02T00:00:00Z",
            "level": "warning",
            "tags": ["frontend"],
            "context": {},
            "host": "testhost",
            "pid": 12347,
        },
    ]

    # Create event files in the correct directory structure
    for event in events:
        ts = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
        day_dir = EVENTS_DIR / ts.strftime("%Y/%m/%d")
        day_dir.mkdir(parents=True, exist_ok=True)
        event_path = day_dir / f"{event['event_id']}.json"
        with open(event_path, "w") as f:
            json.dump(event, f, indent=2)

    return events
