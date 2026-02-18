"""
Tests for crashvault.core module - the data layer.
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path


class TestEnsureDirs:
    """Tests for ensure_dirs function."""

    def test_creates_all_directories(self, crashvault_home):
        """ensure_dirs should create all required directories."""
        from crashvault.core import EVENTS_DIR, LOGS_DIR, ATTACH_DIR

        assert EVENTS_DIR.exists()
        assert LOGS_DIR.exists()
        assert ATTACH_DIR.exists()

    def test_creates_issues_file(self, crashvault_home):
        """ensure_dirs should create an empty issues.json file."""
        from crashvault.core import ISSUES_FILE

        assert ISSUES_FILE.exists()
        with open(ISSUES_FILE) as f:
            assert json.load(f) == []

    def test_creates_config_file(self, crashvault_home):
        """ensure_dirs should create a default config.json file."""
        from crashvault.core import CONFIG_FILE

        assert CONFIG_FILE.exists()
        with open(CONFIG_FILE) as f:
            cfg = json.load(f)
            assert cfg.get("version") == 1

    def test_idempotent(self, crashvault_home):
        """ensure_dirs should be idempotent - calling it twice should work."""
        from crashvault.core import ensure_dirs, ISSUES_FILE

        # Add some data
        with open(ISSUES_FILE, "w") as f:
            json.dump([{"id": 1, "title": "test"}], f)

        # Call ensure_dirs again
        ensure_dirs()

        # Data should be preserved
        with open(ISSUES_FILE) as f:
            issues = json.load(f)
            assert len(issues) == 1
            assert issues[0]["id"] == 1


class TestWriteJsonAtomic:
    """Tests for _write_json_atomic function."""

    def test_writes_valid_json(self, crashvault_home):
        """Should write valid JSON to the specified path."""
        from crashvault.core import _write_json_atomic

        test_path = crashvault_home / "test.json"
        data = {"key": "value", "number": 42, "list": [1, 2, 3]}

        _write_json_atomic(test_path, data)

        with open(test_path) as f:
            result = json.load(f)
            assert result == data

    def test_atomic_write_no_tmp_file_left(self, crashvault_home):
        """No temporary file should be left after a successful write."""
        from crashvault.core import _write_json_atomic

        test_path = crashvault_home / "test.json"
        _write_json_atomic(test_path, {"test": True})

        tmp_path = test_path.with_suffix(".json.tmp")
        assert not tmp_path.exists()

    def test_overwrites_existing_file(self, crashvault_home):
        """Should overwrite existing files."""
        from crashvault.core import _write_json_atomic

        test_path = crashvault_home / "test.json"
        _write_json_atomic(test_path, {"version": 1})
        _write_json_atomic(test_path, {"version": 2})

        with open(test_path) as f:
            result = json.load(f)
            assert result["version"] == 2


class TestEventPathFor:
    """Tests for event_path_for function."""

    def test_correct_path_structure(self, crashvault_home):
        """event_path_for should return path in YYYY/MM/DD/event_id.json format."""
        from crashvault.core import event_path_for, EVENTS_DIR

        ts = datetime(2024, 3, 15, 10, 30, 0, tzinfo=timezone.utc)
        event_id = "test-event-123"

        result = event_path_for(event_id, ts)

        expected = EVENTS_DIR / "2024" / "03" / "15" / "test-event-123.json"
        assert result == expected

    def test_creates_parent_directories(self, crashvault_home):
        """event_path_for should create the necessary parent directories."""
        from crashvault.core import event_path_for

        ts = datetime(2025, 12, 25, 0, 0, 0, tzinfo=timezone.utc)
        event_id = "holiday-event"

        result = event_path_for(event_id, ts)

        assert result.parent.exists()


class TestLoadSaveIssues:
    """Tests for load_issues and save_issues functions."""

    def test_load_empty_issues(self, crashvault_home):
        """Loading from a fresh install should return empty list."""
        from crashvault.core import load_issues

        issues = load_issues()
        assert issues == []

    def test_save_and_load_roundtrip(self, crashvault_home):
        """Issues should survive a save/load cycle unchanged."""
        from crashvault.core import load_issues, save_issues

        test_issues = [
            {"id": 1, "fingerprint": "abc123", "title": "Test", "status": "open"},
            {"id": 2, "fingerprint": "def456", "title": "Test 2", "status": "resolved"},
        ]

        save_issues(test_issues)
        loaded = load_issues()

        assert loaded == test_issues

    def test_load_preserves_order(self, crashvault_home):
        """Issue order should be preserved."""
        from crashvault.core import load_issues, save_issues

        test_issues = [
            {"id": i, "fingerprint": f"fp{i}", "title": f"Issue {i}", "status": "open"}
            for i in range(10)
        ]

        save_issues(test_issues)
        loaded = load_issues()

        assert [i["id"] for i in loaded] == list(range(10))


class TestLoadEvents:
    """Tests for load_events function."""

    def test_load_empty_events(self, crashvault_home):
        """Loading from a fresh install should return empty list."""
        from crashvault.core import load_events

        events = load_events()
        assert events == []

    def test_load_events_from_multiple_days(self, crashvault_home, sample_events):
        """Should load events from multiple date directories."""
        from crashvault.core import load_events

        events = load_events()
        assert len(events) == 3

    def test_skip_corrupted_json(self, crashvault_home):
        """Should gracefully skip corrupted JSON files."""
        from crashvault.core import load_events, EVENTS_DIR, event_path_for
        from datetime import datetime, timezone

        # Create a valid event
        ts = datetime.now(timezone.utc)
        valid_path = event_path_for("valid-event", ts)
        with open(valid_path, "w") as f:
            json.dump({"event_id": "valid-event", "message": "test"}, f)

        # Create a corrupted JSON file
        corrupt_path = valid_path.parent / "corrupted.json"
        with open(corrupt_path, "w") as f:
            f.write("{invalid json content")

        events = load_events()
        assert len(events) == 1
        assert events[0]["event_id"] == "valid-event"


class TestLoadSaveConfig:
    """Tests for load_config and save_config functions."""

    def test_load_default_config(self, crashvault_home):
        """Fresh config should have version 1."""
        from crashvault.core import load_config

        cfg = load_config()
        assert cfg.get("version") == 1

    def test_save_and_load_config_roundtrip(self, crashvault_home):
        """Config should survive a save/load cycle."""
        from crashvault.core import load_config, save_config

        cfg = {
            "version": 1,
            "user": {"name": "Test User", "email": "test@example.com"},
            "custom_setting": True,
        }

        save_config(cfg)
        loaded = load_config()

        assert loaded == cfg

    def test_load_corrupted_config_returns_default(self, crashvault_home):
        """Corrupted config file should return default config."""
        from crashvault.core import load_config, CONFIG_FILE

        # Write corrupted config
        with open(CONFIG_FILE, "w") as f:
            f.write("{broken json")

        cfg = load_config()
        assert cfg == {"version": 1}


class TestGetConfigValue:
    """Tests for get_config_value function."""

    def test_get_existing_key(self, crashvault_home):
        """Should return the value for an existing key."""
        from crashvault.core import save_config, get_config_value

        save_config({"version": 1, "test_key": "test_value"})
        assert get_config_value("test_key") == "test_value"

    def test_get_missing_key_with_default(self, crashvault_home):
        """Should return default for a missing key."""
        from crashvault.core import get_config_value

        assert get_config_value("nonexistent", "default") == "default"

    def test_get_missing_key_without_default(self, crashvault_home):
        """Should return None for a missing key without default."""
        from crashvault.core import get_config_value

        assert get_config_value("nonexistent") is None


class TestGetUserConfig:
    """Tests for get_user_config function."""

    def test_returns_user_config_when_set(self, crashvault_home):
        """Should return user config from config file."""
        from crashvault.core import save_config, get_user_config

        user_cfg = {"name": "John Doe", "email": "john@example.com", "team": "Backend"}
        save_config({"version": 1, "user": user_cfg})

        result = get_user_config()
        assert result == user_cfg

    def test_returns_defaults_when_not_set(self, crashvault_home, monkeypatch):
        """Should return defaults from env vars when user config not set."""
        import platform
        from crashvault.core import get_user_config

        # Clear both env vars first to ensure clean state
        monkeypatch.delenv("USERNAME", raising=False)
        monkeypatch.delenv("USER", raising=False)

        # Set the appropriate env var for the platform
        # The code checks USERNAME first (Windows), then USER (Unix)
        if platform.system() == "Windows":
            monkeypatch.setenv("USERNAME", "testuser")
        else:
            monkeypatch.setenv("USER", "testuser")

        result = get_user_config()
        assert result["name"] == "testuser"
        assert result["email"] == ""
        assert result["team"] == ""