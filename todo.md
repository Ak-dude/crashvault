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

## Future Ideas
- [ ] Support for attachments in webhook notifications
- [ ] Implement alerting rules engine (e.g., "notify if >10 errors/min")
- [ ] Add machine learning for error classification
- [ ] Support for distributed tracing integration
- [ ] Implement data retention policies
- [] Sharing Crashes via MD or JSON
