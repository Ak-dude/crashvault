## Crashvault

Crashvault is a lightweight, local-first crash/error vault with a simple CLI. Log errors, group them into issues, search, export/import, and keep a local history.

## Install

From source:
```
pip install -e .
```

Once installed, the `crashvault` command is available.

## Commands

```
crashvault help
```

```
crashvault list
```

```
crashvault add [ERROR]

```

crashvault kill

## Enhanced usage

- Enriched event logging with levels, tags, and context:

```
crashvault add "Database timeout" --level=error --tag=db --tag=timeout --context service=orders --context region=us-east-1
```

- Search events by level, tag, and text:

```
crashvault search --level=error --tag=db --text="timeout"
```

- Show simple statistics:

```
crashvault stats
```

### Additional commands

- Set status / reopen / rename:
```
crashvault set-status 12 resolved
crashvault reopen 12
crashvault set-title 12 "New clearer title"
```

- Purge a single issue and its events:
```
crashvault purge 12
```

- Garbage collect orphaned events:
```
crashvault gc
```

- Export/Import all data:
```
crashvault export --output backup.json
crashvault import backup.json --mode=merge
```

- Tail events live (with optional filters):
```
crashvault tail --level=error --tag=db --text=timeout
```

- List with filters/sorting:
```
crashvault list --status=open --sort=created_at --desc
```

### Beyond errors: notes, reports, attachments

- Add a quick note:
```
crashvault note "Shipped v0.2.0 to staging" --tag=release
```

- Create a small report:
```
crashvault report --title "Outage resolved" --body "Root cause: bad config" --tag=incident
```

- Attach a file:
```
crashvault attach ./screenshot.png --name ui/screenshot-2025-10-09.png
```

### Auto logging options

- Wrap any command and auto-log on failure:
```
crashvault wrap npm run build
```

- Install a Python exception hook (current process only):
```
python -c "import crashvault.cli as c; c.autolog.main([])"
# or from CLI spawn a Python process and autolog uncaught exceptions in that process
crashvault autolog
```

### Diagnose and AI-assisted fix

- Show code context from a stacktrace event:
```
crashvault diagnose <EVENT_ID>
```

- Ask a local Ollama model for a fix suggestion (configure model via `crashvault config set ollama_model "qwen2.5-coder:7b"`):
```
crashvault ai-fix <EVENT_ID> --model qwen2.5-coder:7b
```

### Notifications

- Send a desktop notification for an event:
```
crashvault notify <EVENT_ID>
```

### Testing integration

- Run tests for your repo (with coverage if available):
```
crashvault test --coverage --path tests/
```

## Configuration

- Data directory: defaults to `~/.crashvault`. Override with environment variable `CRASHVAULT_HOME` or via config file:
```
crashvault config set root "C:/path/to/folder"
```

- View current path:
```
crashvault path
```

- Initialize folders (idempotent):
```
crashvault init
```

## Contributors
Thanks to Creeperkid2014 / AgentArk5
