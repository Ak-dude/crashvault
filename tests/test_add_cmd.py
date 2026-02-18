"""
Tests for crashvault add command.
"""
import json
import hashlib


class TestAddCommand:
    """Tests for the add command."""

    def test_add_creates_new_issue(self, crashvault_home, cli_runner):
        """Adding a new message should create a new issue."""
        from crashvault.cli import cli
        from crashvault.core import load_issues

        result = cli_runner.invoke(cli, ["add", "Test error message"])

        assert result.exit_code == 0
        assert "Created new issue" in result.output

        issues = load_issues()
        assert len(issues) == 1
        assert issues[0]["title"] == "Test error message"
        assert issues[0]["status"] == "open"

    def test_add_creates_event(self, crashvault_home, cli_runner):
        """Adding a message should create an event file."""
        from crashvault.cli import cli
        from crashvault.core import load_events

        cli_runner.invoke(cli, ["add", "Test error message"])

        events = load_events()
        assert len(events) == 1
        assert events[0]["message"] == "Test error message"

    def test_add_same_message_twice_creates_one_issue(self, crashvault_home, cli_runner):
        """Adding the same message twice should create one issue but two events."""
        from crashvault.cli import cli
        from crashvault.core import load_issues, load_events

        cli_runner.invoke(cli, ["add", "Duplicate error"])
        cli_runner.invoke(cli, ["add", "Duplicate error"])

        issues = load_issues()
        events = load_events()

        assert len(issues) == 1
        assert len(events) == 2
        assert all(e["issue_id"] == issues[0]["id"] for e in events)

    def test_add_different_messages_creates_separate_issues(self, crashvault_home, cli_runner):
        """Different messages should create different issues."""
        from crashvault.cli import cli
        from crashvault.core import load_issues

        cli_runner.invoke(cli, ["add", "First error"])
        cli_runner.invoke(cli, ["add", "Second error"])

        issues = load_issues()
        assert len(issues) == 2
        assert issues[0]["fingerprint"] != issues[1]["fingerprint"]

    def test_fingerprint_is_sha1_prefix(self, crashvault_home, cli_runner):
        """Fingerprint should be first 8 chars of SHA1 hash of message."""
        from crashvault.cli import cli
        from crashvault.core import load_issues

        message = "Test error for fingerprint"
        expected_fp = hashlib.sha1(message.encode("utf-8")).hexdigest()[:8]

        cli_runner.invoke(cli, ["add", message])

        issues = load_issues()
        assert issues[0]["fingerprint"] == expected_fp

    def test_add_with_level(self, crashvault_home, cli_runner):
        """Should set the correct level on the event."""
        from crashvault.cli import cli
        from crashvault.core import load_events

        cli_runner.invoke(cli, ["add", "Warning message", "--level", "warning"])

        events = load_events()
        assert events[0]["level"] == "warning"

    def test_add_default_level_is_error(self, crashvault_home, cli_runner):
        """Default level should be 'error'."""
        from crashvault.cli import cli
        from crashvault.core import load_events

        cli_runner.invoke(cli, ["add", "Default level message"])

        events = load_events()
        assert events[0]["level"] == "error"

    def test_add_with_tags(self, crashvault_home, cli_runner):
        """Should set tags on the event."""
        from crashvault.cli import cli
        from crashvault.core import load_events

        cli_runner.invoke(cli, ["add", "Tagged error", "--tag", "backend", "--tag", "api"])

        events = load_events()
        assert set(events[0]["tags"]) == {"backend", "api"}

    def test_add_with_context(self, crashvault_home, cli_runner):
        """Should parse context key=value pairs."""
        from crashvault.cli import cli
        from crashvault.core import load_events

        cli_runner.invoke(cli, [
            "add", "Error with context",
            "--context", "user_id=123",
            "--context", "request_id=abc-def"
        ])

        events = load_events()
        assert events[0]["context"]["user_id"] == "123"
        assert events[0]["context"]["request_id"] == "abc-def"

    def test_add_with_stack_trace(self, crashvault_home, cli_runner):
        """Should store stack trace in the event."""
        from crashvault.cli import cli
        from crashvault.core import load_events

        stack = "File \"test.py\", line 10\n    raise Exception('test')"
        cli_runner.invoke(cli, ["add", "Error with stack", "--stack", stack])

        events = load_events()
        assert events[0]["stacktrace"] == stack

    def test_add_truncates_long_title(self, crashvault_home, cli_runner):
        """Issue title should be truncated to 80 chars."""
        from crashvault.cli import cli
        from crashvault.core import load_issues

        long_message = "A" * 100

        cli_runner.invoke(cli, ["add", long_message])

        issues = load_issues()
        assert len(issues[0]["title"]) == 80
        assert issues[0]["title"] == "A" * 80

    def test_event_has_required_fields(self, crashvault_home, cli_runner):
        """Event should have all required fields."""
        from crashvault.cli import cli
        from crashvault.core import load_events

        cli_runner.invoke(cli, ["add", "Test message"])

        events = load_events()
        event = events[0]

        required_fields = [
            "event_id", "issue_id", "message", "stacktrace",
            "timestamp", "level", "tags", "context", "host", "pid"
        ]
        for field in required_fields:
            assert field in event, f"Missing field: {field}"

    def test_event_timestamp_is_iso_format(self, crashvault_home, cli_runner):
        """Event timestamp should be in ISO format with Z suffix."""
        from crashvault.cli import cli
        from crashvault.core import load_events

        cli_runner.invoke(cli, ["add", "Test message"])

        events = load_events()
        timestamp = events[0]["timestamp"]

        assert timestamp.endswith("Z")
        # Should be parseable
        from datetime import datetime
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

    def test_issue_id_increments(self, crashvault_home, cli_runner):
        """Issue IDs should increment sequentially."""
        from crashvault.cli import cli
        from crashvault.core import load_issues

        cli_runner.invoke(cli, ["add", "First error"])
        cli_runner.invoke(cli, ["add", "Second error"])
        cli_runner.invoke(cli, ["add", "Third error"])

        issues = load_issues()
        ids = [i["id"] for i in issues]
        assert ids == [1, 2, 3]
