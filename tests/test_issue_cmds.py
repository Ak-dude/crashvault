"""
Tests for issue state management commands (resolve, reopen, set-status, set-title, purge).
"""
import json


class TestResolveCommand:
    """Tests for the resolve command."""

    def test_resolve_open_issue(self, crashvault_home, cli_runner, sample_issues):
        """Should mark an open issue as resolved."""
        from crashvault.cli import cli
        from crashvault.core import load_issues

        result = cli_runner.invoke(cli, ["resolve", "1"])

        assert result.exit_code == 0
        assert "resolved" in result.output.lower()

        issues = load_issues()
        issue = next(i for i in issues if i["id"] == 1)
        assert issue["status"] == "resolved"

    def test_resolve_nonexistent_issue(self, crashvault_home, cli_runner):
        """Should show error for nonexistent issue."""
        from crashvault.cli import cli

        result = cli_runner.invoke(cli, ["resolve", "999"])

        assert "not found" in result.output.lower()

    def test_resolve_already_resolved_issue(self, crashvault_home, cli_runner, sample_issues):
        """Should still work on already resolved issues."""
        from crashvault.cli import cli
        from crashvault.core import load_issues

        # Issue 2 is already resolved in sample_issues
        result = cli_runner.invoke(cli, ["resolve", "2"])

        assert result.exit_code == 0
        issues = load_issues()
        issue = next(i for i in issues if i["id"] == 2)
        assert issue["status"] == "resolved"


class TestReopenCommand:
    """Tests for the reopen command."""

    def test_reopen_resolved_issue(self, crashvault_home, cli_runner, sample_issues):
        """Should reopen a resolved issue."""
        from crashvault.cli import cli
        from crashvault.core import load_issues

        # Issue 2 is resolved in sample_issues
        result = cli_runner.invoke(cli, ["reopen", "2"])

        assert result.exit_code == 0
        assert "reopened" in result.output.lower()

        issues = load_issues()
        issue = next(i for i in issues if i["id"] == 2)
        assert issue["status"] == "open"

    def test_reopen_ignored_issue(self, crashvault_home, cli_runner, sample_issues):
        """Should reopen an ignored issue."""
        from crashvault.cli import cli
        from crashvault.core import load_issues

        # Issue 3 is ignored in sample_issues
        result = cli_runner.invoke(cli, ["reopen", "3"])

        assert result.exit_code == 0
        issues = load_issues()
        issue = next(i for i in issues if i["id"] == 3)
        assert issue["status"] == "open"

    def test_reopen_nonexistent_issue(self, crashvault_home, cli_runner):
        """Should show error for nonexistent issue."""
        from crashvault.cli import cli

        result = cli_runner.invoke(cli, ["reopen", "999"])

        assert "not found" in result.output.lower()


class TestSetStatusCommand:
    """Tests for the set-status command."""

    def test_set_status_to_open(self, crashvault_home, cli_runner, sample_issues):
        """Should set status to open."""
        from crashvault.cli import cli
        from crashvault.core import load_issues

        result = cli_runner.invoke(cli, ["set-status", "2", "open"])

        assert result.exit_code == 0
        issues = load_issues()
        issue = next(i for i in issues if i["id"] == 2)
        assert issue["status"] == "open"

    def test_set_status_to_resolved(self, crashvault_home, cli_runner, sample_issues):
        """Should set status to resolved."""
        from crashvault.cli import cli
        from crashvault.core import load_issues

        result = cli_runner.invoke(cli, ["set-status", "1", "resolved"])

        assert result.exit_code == 0
        issues = load_issues()
        issue = next(i for i in issues if i["id"] == 1)
        assert issue["status"] == "resolved"

    def test_set_status_to_ignored(self, crashvault_home, cli_runner, sample_issues):
        """Should set status to ignored."""
        from crashvault.cli import cli
        from crashvault.core import load_issues

        result = cli_runner.invoke(cli, ["set-status", "1", "ignored"])

        assert result.exit_code == 0
        issues = load_issues()
        issue = next(i for i in issues if i["id"] == 1)
        assert issue["status"] == "ignored"

    def test_set_status_case_insensitive(self, crashvault_home, cli_runner, sample_issues):
        """Status values should be case insensitive."""
        from crashvault.cli import cli
        from crashvault.core import load_issues

        result = cli_runner.invoke(cli, ["set-status", "1", "RESOLVED"])

        assert result.exit_code == 0
        issues = load_issues()
        issue = next(i for i in issues if i["id"] == 1)
        assert issue["status"] == "resolved"

    def test_set_status_invalid_status(self, crashvault_home, cli_runner, sample_issues):
        """Should reject invalid status values."""
        from crashvault.cli import cli

        result = cli_runner.invoke(cli, ["set-status", "1", "invalid"])

        # Click should reject invalid choice
        assert result.exit_code != 0

    def test_set_status_nonexistent_issue(self, crashvault_home, cli_runner):
        """Should show error for nonexistent issue."""
        from crashvault.cli import cli

        result = cli_runner.invoke(cli, ["set-status", "999", "open"])

        assert "not found" in result.output.lower()


class TestSetTitleCommand:
    """Tests for the set-title command."""

    def test_set_title(self, crashvault_home, cli_runner, sample_issues):
        """Should update the issue title."""
        from crashvault.cli import cli
        from crashvault.core import load_issues

        result = cli_runner.invoke(cli, ["set-title", "1", "New title for issue"])

        assert result.exit_code == 0
        issues = load_issues()
        issue = next(i for i in issues if i["id"] == 1)
        assert issue["title"] == "New title for issue"

    def test_set_title_truncates_long_title(self, crashvault_home, cli_runner, sample_issues):
        """Should truncate title to 200 chars."""
        from crashvault.cli import cli
        from crashvault.core import load_issues

        long_title = "X" * 250

        result = cli_runner.invoke(cli, ["set-title", "1", long_title])

        assert result.exit_code == 0
        issues = load_issues()
        issue = next(i for i in issues if i["id"] == 1)
        assert len(issue["title"]) == 200

    def test_set_title_nonexistent_issue(self, crashvault_home, cli_runner):
        """Should show error for nonexistent issue."""
        from crashvault.cli import cli

        result = cli_runner.invoke(cli, ["set-title", "999", "New title"])

        assert "not found" in result.output.lower()


class TestPurgeCommand:
    """Tests for the purge command."""

    def test_purge_issue_removes_from_list(self, crashvault_home, cli_runner, sample_issues, sample_events):
        """Purge should remove the issue from the list."""
        from crashvault.cli import cli
        from crashvault.core import load_issues

        # Confirm the purge
        result = cli_runner.invoke(cli, ["purge", "1"], input="y\n")

        assert result.exit_code == 0
        issues = load_issues()
        assert not any(i["id"] == 1 for i in issues)
        assert len(issues) == 2  # 2 remaining from sample_issues

    def test_purge_deletes_events(self, crashvault_home, cli_runner, sample_issues, sample_events):
        """Purge should delete associated event files."""
        from crashvault.cli import cli
        from crashvault.core import load_events

        # Issue 1 has 2 events in sample_events
        result = cli_runner.invoke(cli, ["purge", "1"], input="y\n")

        assert result.exit_code == 0
        events = load_events()
        # Only event-003 (issue_id=2) should remain
        assert len(events) == 1
        assert events[0]["event_id"] == "event-003"

    def test_purge_aborted(self, crashvault_home, cli_runner, sample_issues):
        """Purge should be abortable."""
        from crashvault.cli import cli
        from crashvault.core import load_issues

        result = cli_runner.invoke(cli, ["purge", "1"], input="n\n")

        # Issue should still exist
        issues = load_issues()
        assert any(i["id"] == 1 for i in issues)

    def test_purge_nonexistent_issue(self, crashvault_home, cli_runner):
        """Should show error for nonexistent issue."""
        from crashvault.cli import cli

        result = cli_runner.invoke(cli, ["purge", "999"], input="y\n")

        assert "not found" in result.output.lower()


class TestKillCommand:
    """Tests for the kill command (wipes all data)."""

    def test_kill_removes_all_issues(self, crashvault_home, cli_runner, sample_issues):
        """Kill should remove all issues."""
        from crashvault.cli import cli
        from crashvault.core import load_issues

        result = cli_runner.invoke(cli, ["kill"], input="y\n")

        assert result.exit_code == 0
        issues = load_issues()
        assert issues == []

    def test_kill_removes_all_events(self, crashvault_home, cli_runner, sample_issues, sample_events):
        """Kill should remove all event files."""
        from crashvault.cli import cli
        from crashvault.core import load_events

        result = cli_runner.invoke(cli, ["kill"], input="y\n")

        assert result.exit_code == 0
        events = load_events()
        assert events == []

    def test_kill_aborted(self, crashvault_home, cli_runner, sample_issues):
        """Kill should be abortable."""
        from crashvault.cli import cli
        from crashvault.core import load_issues

        result = cli_runner.invoke(cli, ["kill"], input="n\n")

        # Issues should still exist
        issues = load_issues()
        assert len(issues) == 3