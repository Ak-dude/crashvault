# Crashvault TODO

## High Priority
- [ ] Implement batch analyze command (build/lib files already present)
- [ ] Implement code review command (build/lib files already present)
- [ ] Complete webhook feature integration (prototype added in commit 5ae3738)
- [ ] Test and finalize rich styling across all commands
- [ ] Add comprehensive error handling for server endpoints

## Documentation
- [ ] Write usage guide for batch analyze feature
- [ ] Create webhook integration examples for more frameworks (Django, Express, Flask)
- [ ] Add troubleshooting section to README
- [ ] Document CHANGES_SUMMARY.md format and usage

## Features
- [ ] Add filtering options to wrap_cmd.py (by exit code, specific tags)
- [ ] Implement batch operations for issue management
- [ ] Add export/import for individual issues
- [ ] Create interactive TUI for browsing issues
- [ ] Add support for custom severity levels
- [ ] Implement issue deduplication based on stacktrace similarity
- [ ] Add rate limiting for webhook notifications
- [ ] Support for custom webhook templates

## Server & API
- [ ] Add authentication/API key support for server endpoints
- [ ] Implement webhook retry logic with exponential backoff
- [ ] Add metrics endpoint for monitoring
- [ ] Support for CORS configuration
- [ ] Add request rate limiting
- [ ] Implement server clustering/horizontal scaling support

## Testing & Quality
- [ ] Write unit tests for webhook delivery
- [ ] Add integration tests for server endpoints
- [ ] Test batch analyze command functionality
- [ ] Add test coverage for code review command
- [ ] Create end-to-end tests for CLI workflows
- [ ] Add performance benchmarks for large event volumes

## Developer Experience
- [ ] Add shell completion scripts (bash, zsh, fish)
- [ ] Create VSCode extension for inline error viewing
- [ ] Add pre-commit hooks for code quality
- [ ] Implement plugin system for custom commands
- [ ] Add debug mode with verbose logging

## Cleanup
- [ ] Commit or remove untracked build/lib files
- [ ] Review and finalize RICH_STYLING.md documentation
- [ ] Clean up __pycache__ files from git tracking
- [ ] Standardize error message formatting across commands
- [ ] Refactor duplicate code in command files

## Style Guide

### Naming Conventions
- **Functions/variables:** `snake_case` — e.g. `load_issues`, `event_count`
- **Classes:** `PascalCase` — e.g. `WebhookConfig`, `DiscordWebhook`
- **Constants:** `UPPER_SNAKE_CASE` — e.g. `ROOT`, `ISSUES_FILE`, `DEFAULT_PORT`
- **Private helpers:** single leading underscore — e.g. `_write_json_atomic`, `_extract_frames`
- **Command files:** `<verb>_cmd.py` — e.g. `add_cmd.py`, `kill_cmd.py`, `set_status_cmd.py`
- **Webhook provider files:** `<provider>.py` — e.g. `discord.py`, `slack.py`

### Imports
- Comma-separated one-liners are acceptable in command files: `import click, json, os`
- Infrastructure/library files should use separate-line imports, stdlib before local
- Relative imports use `..` from `commands/` up to the package root
- Deferred imports inside functions are fine to avoid circular dependencies

### String Formatting
- Always use **f-strings** — never `.format()` or `%`
- Log messages use pipe-separated key=value format: `logger.info(f"event recorded | issue_id={id} | level={level}")`
- Timestamps: UTC ISO 8601 with `Z` suffix — `datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")`

### CLI Commands (Click)
- `@click.command(name="hyphen-name")` with `def underscore_name():`
- `@click.argument` for required positional params; `@click.option` for optional
- `case_sensitive=False` on all `click.Choice` options
- `show_default=True` on options with meaningful defaults
- `raise click.ClickException("message")` for errors, `click.UsageError` for bad usage
- `@click.confirmation_option(prompt="...")` for destructive operations

### Rich Output
- All terminal output through `console.print()` with f-strings and Rich markup
- Use `click.echo()` only for raw data output (JSON export, subprocess passthrough)
- Semantic markup tags:
  - `[success]` — successful operations
  - `[error]` — error messages
  - `[warning]` — non-critical warnings
  - `[info]` — informational output
  - `[highlight]` — important values (IDs, paths, keys)
  - `[primary]` — open issue status
  - `[secondary]` — timestamps, secondary info
  - `[muted]` — decorators, less important text
  - `[danger]` — critical/destructive actions

### Error Handling
- `except Exception: pass` for non-critical optional paths (e.g. webhook dispatch)
- `except Exception: continue` in file-scanning loops
- Specific exception types (`URLError`, `JSONDecodeError`) only in webhooks/server layer
- Never use bare `except:` — always `except Exception:`

### Data & Persistence
- All JSON writes use atomic pattern: write to `.tmp` then `os.replace()`
- Always `json.dump(..., indent=2)`
- All persistence goes through `core.py` helpers — commands never write files directly
- Event IDs: `str(uuid.uuid4())`
- Issue fingerprints: `hashlib.sha1(msg.encode("utf-8")).hexdigest()[:8]`

### Docstrings
- Click commands: single imperative sentence (doubles as `--help` text)
- Modules: plain prose paragraph(s), no reST or NumPy style
- Private helpers: docstrings optional
- Multi-line command docstrings may include an `Examples:` block

### Type Hints
- Required in `webhooks/` and `server.py`
- Optional in `commands/` and `core.py`
- Use `from typing import Any, Dict, List, Optional, Type` as needed
- Dataclasses with typed fields for structured data (`webhooks/base.py`)

### Module Organization
- `core.py` is the single source of truth for paths, config, and JSON persistence
- `cli.py` handles only command registration via `cli.add_command()`
- One file per CLI command in `commands/`, one file per webhook provider in `webhooks/`
- `__init__.py` files should be minimal

## Future Ideas
- [ ] Web dashboard for viewing issues
- [ ] Support for attachments in webhook notifications
- [ ] Implement alerting rules engine (e.g., "notify if >10 errors/min")
- [ ] Add machine learning for error classification
- [ ] Support for distributed tracing integration
- [ ] Mobile app for error monitoring
- [ ] Implement data retention policies
