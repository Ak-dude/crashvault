"""
Tests for crashvault wrap command.
Cross-platform compatible (Windows, Linux, macOS).
"""
import sys
import platform


class TestWrapCommand:
    """Tests for the wrap command."""

    def test_wrap_successful_command(self, crashvault_home, cli_runner):
        """Successful command should pass through stdout and not create event."""
        from crashvault.cli import cli
        from crashvault.core import load_events

        # Use Python to print - works on all platforms
        result = cli_runner.invoke(cli, [
            "wrap", "--", sys.executable, "-c", "print('hello world')"
        ])

        assert result.exit_code == 0
        assert "hello world" in result.output

        # No event should be created for successful command
        events = load_events()
        assert len(events) == 0

    def test_wrap_failed_command_creates_event(self, crashvault_home, cli_runner):
        """Failed command should create an error event."""
        from crashvault.cli import cli
        from crashvault.core import load_events

        # Use Python to exit with error - works on all platforms
        result = cli_runner.invoke(cli, [
            "wrap", "--", sys.executable, "-c", "import sys; sys.exit(1)"
        ])

        assert result.exit_code != 0

        events = load_events()
        assert len(events) == 1
        assert "Command failed" in events[0]["message"]
        assert events[0]["issue_id"] == 0  # Wrap events have issue_id=0

    def test_wrap_captures_exit_code(self, crashvault_home, cli_runner):
        """Should preserve the original command's exit code."""
        from crashvault.cli import cli

        # Python exit with specific code - works on all platforms
        result = cli_runner.invoke(cli, [
            "wrap", "--", sys.executable, "-c", "import sys; sys.exit(42)"
        ])

        assert result.exit_code == 42

    def test_wrap_captures_stderr_as_stacktrace(self, crashvault_home, cli_runner):
        """stderr from failed command should be captured as stacktrace."""
        from crashvault.cli import cli
        from crashvault.core import load_events

        # Python write to stderr and exit - works on all platforms
        result = cli_runner.invoke(cli, [
            "wrap", "--", sys.executable, "-c",
            "import sys; sys.stderr.write('error output\\n'); sys.exit(1)"
        ])

        events = load_events()
        assert len(events) == 1
        assert "error output" in events[0]["stacktrace"]

    def test_wrap_with_custom_level(self, crashvault_home, cli_runner):
        """Should use custom level when specified."""
        from crashvault.cli import cli
        from crashvault.core import load_events

        result = cli_runner.invoke(cli, [
            "wrap", "--level", "critical", "--",
            sys.executable, "-c", "import sys; sys.exit(1)"
        ])

        events = load_events()
        assert events[0]["level"] == "critical"

    def test_wrap_default_level_is_error(self, crashvault_home, cli_runner):
        """Default level should be 'error'."""
        from crashvault.cli import cli
        from crashvault.core import load_events

        result = cli_runner.invoke(cli, [
            "wrap", "--", sys.executable, "-c", "import sys; sys.exit(1)"
        ])

        events = load_events()
        assert events[0]["level"] == "error"

    def test_wrap_adds_wrap_tag(self, crashvault_home, cli_runner):
        """Should automatically add 'wrap' tag to events."""
        from crashvault.cli import cli
        from crashvault.core import load_events

        result = cli_runner.invoke(cli, [
            "wrap", "--", sys.executable, "-c", "import sys; sys.exit(1)"
        ])

        events = load_events()
        assert "wrap" in events[0]["tags"]

    def test_wrap_with_custom_tags(self, crashvault_home, cli_runner):
        """Should include custom tags plus 'wrap' tag."""
        from crashvault.cli import cli
        from crashvault.core import load_events

        result = cli_runner.invoke(cli, [
            "wrap", "--tag", "build", "--tag", "ci", "--",
            sys.executable, "-c", "import sys; sys.exit(1)"
        ])

        events = load_events()
        assert set(events[0]["tags"]) == {"wrap", "build", "ci"}

    def test_wrap_stores_return_code_in_context(self, crashvault_home, cli_runner):
        """Should store return code in event context."""
        from crashvault.cli import cli
        from crashvault.core import load_events

        result = cli_runner.invoke(cli, [
            "wrap", "--", sys.executable, "-c", "import sys; sys.exit(5)"
        ])

        events = load_events()
        assert events[0]["context"]["returncode"] == 5

    def test_wrap_message_includes_command(self, crashvault_home, cli_runner):
        """Event message should include the failed command."""
        from crashvault.cli import cli
        from crashvault.core import load_events

        result = cli_runner.invoke(cli, [
            "wrap", "--", sys.executable, "-c", "import sys; sys.exit(1)"
        ])

        events = load_events()
        assert "sys.exit(1)" in events[0]["message"]

    def test_wrap_no_command_error(self, crashvault_home, cli_runner):
        """Should error when no command provided."""
        from crashvault.cli import cli

        result = cli_runner.invoke(cli, ["wrap"])

        assert result.exit_code != 0
        assert "command" in result.output.lower() or "usage" in result.output.lower()

    def test_wrap_passes_stdout_on_failure(self, crashvault_home, cli_runner):
        """Should pass through stdout even on failure."""
        from crashvault.cli import cli

        result = cli_runner.invoke(cli, [
            "wrap", "--", sys.executable, "-c",
            "print('stdout msg'); import sys; sys.exit(1)"
        ])

        assert "stdout msg" in result.output

    def test_wrap_passes_stderr_on_failure(self, crashvault_home, cli_runner):
        """Should pass through stderr on failure."""
        from crashvault.cli import cli

        result = cli_runner.invoke(cli, [
            "wrap", "--", sys.executable, "-c",
            "import sys; sys.stderr.write('stderr msg\\n'); sys.exit(1)"
        ])

        assert "stderr msg" in result.output

    def test_wrap_event_has_host(self, crashvault_home, cli_runner):
        """Event should have host field."""
        from crashvault.cli import cli
        from crashvault.core import load_events

        result = cli_runner.invoke(cli, [
            "wrap", "--", sys.executable, "-c", "import sys; sys.exit(1)"
        ])

        events = load_events()
        assert events[0]["host"] is not None
        assert len(events[0]["host"]) > 0

    def test_wrap_event_has_timestamp(self, crashvault_home, cli_runner):
        """Event should have ISO timestamp."""
        from crashvault.cli import cli
        from crashvault.core import load_events

        result = cli_runner.invoke(cli, [
            "wrap", "--", sys.executable, "-c", "import sys; sys.exit(1)"
        ])

        events = load_events()
        timestamp = events[0]["timestamp"]
        assert timestamp.endswith("Z")

    def test_wrap_command_with_arguments(self, crashvault_home, cli_runner):
        """Should handle commands with multiple arguments."""
        from crashvault.cli import cli

        result = cli_runner.invoke(cli, [
            "wrap", "--", sys.executable, "-c",
            "import sys; print(' '.join(sys.argv[1:]))", "arg1", "arg2", "arg3"
        ])

        assert result.exit_code == 0
        assert "arg1 arg2 arg3" in result.output

    def test_wrap_with_multiline_output(self, crashvault_home, cli_runner):
        """Should handle commands with multiline output."""
        from crashvault.cli import cli

        result = cli_runner.invoke(cli, [
            "wrap", "--", sys.executable, "-c",
            "for i in range(5): print(f'line{i}')"
        ])

        assert result.exit_code == 0
        assert "line0" in result.output
        assert "line4" in result.output

    def test_wrap_with_exception_traceback(self, crashvault_home, cli_runner):
        """Should capture Python tracebacks in stderr."""
        from crashvault.cli import cli
        from crashvault.core import load_events

        result = cli_runner.invoke(cli, [
            "wrap", "--", sys.executable, "-c",
            "raise ValueError('test error message')"
        ])

        assert result.exit_code != 0
        events = load_events()
        assert len(events) == 1
        # Python traceback should be in stderr/stacktrace
        assert "ValueError" in events[0]["stacktrace"] or "ValueError" in result.output
