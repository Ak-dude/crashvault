## Crashvault

Crashvault is a lightweight, local-first crash/error vault with a simple CLI. Log errors, group them into issues, search, export/import, and keep a local history.

## Install

From source:
```
pip install -e .
```

Once installed, the `crashvault` command is available.

### First-time setup

After installation, run the setup command to initialize your configuration:
```
crashvault setup
```

This creates `~/.crashvault/config.json` with default settings for:
- User information (name, email, team)
- AI provider settings (Ollama, OpenAI, Anthropic, Gemini)
- Notification preferences
- Storage configuration

To use Gemini API features, add your API key to the config:
```json
{
  "ai": {
    "provider": "gemini",
    "gemini": {
      "api_key": "your-api-key-here",
      "model": "gemini-1.5-pro"
    }
  }
}
```
Get your API key from: https://makersuite.google.com/app/apikey

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

- Ask AI for a fix suggestion (supports Ollama and Gemini):
```
# Using default provider from config
crashvault ai-fix <EVENT_ID>

# Using Ollama (local)
crashvault ai-fix <EVENT_ID> --provider ollama --model qwen2.5-coder:7b

# Using Gemini (cloud)
crashvault ai-fix <EVENT_ID> --provider gemini --model gemini-1.5-pro
```

### AI-powered code reviews

- Review a file:
```
crashvault code-review --file src/main.py
```

- Review code related to an error:
```
crashvault code-review --error <EVENT_ID>
```

- Review uncommitted git changes:
```
crashvault code-review --diff
```

- Review a specific commit:
```
crashvault code-review --commit HEAD
crashvault code-review --commit abc123
```

### Batch error analysis

- Analyze multiple errors to find patterns:
```
# Analyze all open errors
crashvault batch-analyze --status open --limit 20

# Analyze critical/error level events
crashvault batch-analyze --level error --limit 15

# Analyze errors with specific tags
crashvault batch-analyze --tag database --tag timeout --limit 10
```

This command uses AI to identify:
- Common patterns across multiple errors
- Potential root causes affecting multiple issues
- Priority recommendations for which errors to fix first
- Preventive measures to avoid similar issues

### Generate formatted reports

- Generate reports in various formats:
```
# Markdown report (default)
crashvault generate-report --format markdown --output report.md

# HTML report with styling
crashvault generate-report --format html --output report.html

# JSON report for programmatic processing
crashvault generate-report --format json --output report.json

# Filter reports by status, level, or tags
crashvault generate-report --format html --status open --level error --output errors.html
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
