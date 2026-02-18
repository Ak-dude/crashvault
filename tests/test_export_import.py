"""
Tests for export and import commands.
"""
import json
from pathlib import Path


class TestExportCommand:
    """Tests for the export command."""

    def test_export_to_stdout(self, crashvault_home, cli_runner, sample_issues, sample_events):
        """Export should output JSON to stdout when no file specified."""
        from crashvault.cli import cli

        result = cli_runner.invoke(cli, ["export"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "version" in data
        assert "exported_at" in data
        assert "issues" in data
        assert "events" in data

    def test_export_has_correct_structure(self, crashvault_home, cli_runner, sample_issues, sample_events):
        """Export JSON should have the correct structure."""
        from crashvault.cli import cli

        result = cli_runner.invoke(cli, ["export"])
        data = json.loads(result.output)

        assert data["version"] == 1
        assert len(data["issues"]) == 3
        assert len(data["events"]) == 3

    def test_export_to_file(self, crashvault_home, cli_runner, sample_issues, sample_events, tmp_path):
        """Export should write to file when specified."""
        from crashvault.cli import cli

        output_file = tmp_path / "export.json"
        result = cli_runner.invoke(cli, ["export", "--output", str(output_file)])

        assert result.exit_code == 0
        assert output_file.exists()

        data = json.loads(output_file.read_text())
        assert len(data["issues"]) == 3

    def test_export_empty_vault(self, crashvault_home, cli_runner):
        """Export of empty vault should have empty arrays."""
        from crashvault.cli import cli

        result = cli_runner.invoke(cli, ["export"])
        data = json.loads(result.output)

        assert data["issues"] == []
        assert data["events"] == []

    def test_exported_at_is_iso_format(self, crashvault_home, cli_runner, sample_issues):
        """exported_at should be in ISO format with Z suffix."""
        from crashvault.cli import cli

        result = cli_runner.invoke(cli, ["export"])
        data = json.loads(result.output)

        assert data["exported_at"].endswith("Z")


class TestImportCommand:
    """Tests for the import command."""

    def test_import_merge_mode_adds_new_issues(self, crashvault_home, cli_runner, sample_issues, tmp_path):
        """Merge mode should add new issues without removing existing."""
        from crashvault.cli import cli
        from crashvault.core import load_issues

        # Create an import file with a new issue
        import_data = {
            "version": 1,
            "issues": [
                {
                    "fingerprint": "new12345",
                    "title": "New imported issue",
                    "status": "open",
                    "created_at": "2024-02-01T00:00:00Z"
                }
            ],
            "events": []
        }
        import_file = tmp_path / "import.json"
        import_file.write_text(json.dumps(import_data))

        result = cli_runner.invoke(cli, ["import", str(import_file)])

        assert result.exit_code == 0
        issues = load_issues()
        # Should have 3 original + 1 new = 4
        assert len(issues) == 4
        assert any(i["title"] == "New imported issue" for i in issues)

    def test_import_merge_mode_updates_existing(self, crashvault_home, cli_runner, sample_issues, tmp_path):
        """Merge mode should update existing issues by fingerprint."""
        from crashvault.cli import cli
        from crashvault.core import load_issues

        # Import file with same fingerprint as sample issue 1
        import_data = {
            "version": 1,
            "issues": [
                {
                    "fingerprint": "abc12345",  # Same as sample issue 1
                    "title": "Updated title",
                    "status": "resolved",
                }
            ],
            "events": []
        }
        import_file = tmp_path / "import.json"
        import_file.write_text(json.dumps(import_data))

        result = cli_runner.invoke(cli, ["import", str(import_file)])

        assert result.exit_code == 0
        issues = load_issues()
        issue = next(i for i in issues if i["fingerprint"] == "abc12345")
        assert issue["title"] == "Updated title"
        assert issue["status"] == "resolved"

    def test_import_replace_mode_wipes_existing(self, crashvault_home, cli_runner, sample_issues, sample_events, tmp_path):
        """Replace mode should wipe existing data."""
        from crashvault.cli import cli
        from crashvault.core import load_issues, load_events

        import_data = {
            "version": 1,
            "issues": [
                {
                    "fingerprint": "replace1",
                    "title": "Replacement issue",
                    "status": "open",
                }
            ],
            "events": []
        }
        import_file = tmp_path / "import.json"
        import_file.write_text(json.dumps(import_data))

        result = cli_runner.invoke(cli, ["import", str(import_file), "--mode", "replace"])

        assert result.exit_code == 0
        issues = load_issues()
        events = load_events()
        # Only the imported issue should exist
        assert len(issues) == 1
        assert issues[0]["title"] == "Replacement issue"

    def test_import_creates_events(self, crashvault_home, cli_runner, sample_issues, tmp_path):
        """Import should create event files."""
        from crashvault.cli import cli
        from crashvault.core import load_events

        import_data = {
            "version": 1,
            "issues": [],
            "events": [
                {
                    "issue_id": 1,  # Existing issue
                    "message": "Imported event",
                    "level": "warning",
                    "tags": ["imported"],
                    "context": {"source": "import"}
                }
            ]
        }
        import_file = tmp_path / "import.json"
        import_file.write_text(json.dumps(import_data))

        result = cli_runner.invoke(cli, ["import", str(import_file)])

        assert result.exit_code == 0
        events = load_events()
        imported_event = next((e for e in events if e["message"] == "Imported event"), None)
        assert imported_event is not None
        assert imported_event["level"] == "warning"
        assert imported_event["tags"] == ["imported"]

    def test_import_orphan_events_creates_issues(self, crashvault_home, cli_runner, tmp_path):
        """Events without matching issues should auto-create issues."""
        from crashvault.cli import cli
        from crashvault.core import load_issues, load_events

        import_data = {
            "version": 1,
            "issues": [],
            "events": [
                {
                    "issue_id": 999,  # Non-existent issue
                    "message": "Orphan event message",
                    "level": "error",
                }
            ]
        }
        import_file = tmp_path / "import.json"
        import_file.write_text(json.dumps(import_data))

        result = cli_runner.invoke(cli, ["import", str(import_file)])

        assert result.exit_code == 0
        issues = load_issues()
        events = load_events()
        # Issue should be auto-created
        assert len(issues) == 1
        assert len(events) == 1

    def test_import_preserves_issue_ids(self, crashvault_home, cli_runner, tmp_path):
        """Imported issues should get new sequential IDs."""
        from crashvault.cli import cli
        from crashvault.core import load_issues

        import_data = {
            "version": 1,
            "issues": [
                {"fingerprint": "fp1", "title": "Issue 1"},
                {"fingerprint": "fp2", "title": "Issue 2"},
            ],
            "events": []
        }
        import_file = tmp_path / "import.json"
        import_file.write_text(json.dumps(import_data))

        result = cli_runner.invoke(cli, ["import", str(import_file)])

        assert result.exit_code == 0
        issues = load_issues()
        ids = sorted(i["id"] for i in issues)
        assert ids == [1, 2]


class TestExportImportRoundtrip:
    """Tests for export/import roundtrip scenarios."""

    def test_full_roundtrip(self, crashvault_home, cli_runner, sample_issues, sample_events, tmp_path):
        """Export and re-import should preserve data."""
        from crashvault.cli import cli
        from crashvault.core import load_issues, load_events

        # Export
        export_file = tmp_path / "roundtrip.json"
        cli_runner.invoke(cli, ["export", "--output", str(export_file)])

        # Clear everything
        cli_runner.invoke(cli, ["kill"], input="y\n")
        assert load_issues() == []

        # Import
        result = cli_runner.invoke(cli, ["import", str(export_file)])

        assert result.exit_code == 0
        issues = load_issues()
        events = load_events()

        # Should have same number of issues
        assert len(issues) == 3
        # Events will be re-created with new IDs
        assert len(events) == 3

    def test_roundtrip_preserves_fingerprints(self, crashvault_home, cli_runner, sample_issues, tmp_path):
        """Roundtrip should preserve issue fingerprints."""
        from crashvault.cli import cli
        from crashvault.core import load_issues

        original_fps = {i["fingerprint"] for i in sample_issues}

        # Export
        export_file = tmp_path / "roundtrip.json"
        cli_runner.invoke(cli, ["export", "--output", str(export_file)])

        # Clear and import
        cli_runner.invoke(cli, ["kill"], input="y\n")
        cli_runner.invoke(cli, ["import", str(export_file)])

        # Check fingerprints
        issues = load_issues()
        imported_fps = {i["fingerprint"] for i in issues}
        assert imported_fps == original_fps
