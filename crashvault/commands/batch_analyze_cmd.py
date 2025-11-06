"""Batch analyze multiple errors to find patterns."""
import click, json
from ..core import load_issues, load_events, get_ai_config
from rich.console import Console
from rich.table import Table

console = Console()

BATCH_ANALYSIS_PROMPT = """
You are a senior engineer analyzing multiple error events to find patterns and root causes.

Analyze the following errors and provide:
1. Common patterns across errors
2. Potential systemic issues
3. Priority recommendations (which errors to fix first)
4. Root cause analysis
5. Preventive measures

ERRORS:
{errors_json}

SUMMARY STATISTICS:
- Total errors analyzed: {total_count}
- Unique error types: {unique_count}
- Time range: {time_range}
- Most common error levels: {level_distribution}
"""


def _call_gemini_api(prompt, model, api_key, timeout):
    """Call Gemini API for batch analysis."""
    try:
        import requests
    except ImportError:
        raise click.ClickException("requests library required for Gemini API. Install with: pip install requests")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    headers = {
        "Content-Type": "application/json",
    }

    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 8192,
        }
    }

    try:
        response = requests.post(
            f"{url}?key={api_key}",
            headers=headers,
            json=payload,
            timeout=timeout
        )
        response.raise_for_status()

        result = response.json()
        if "candidates" in result and len(result["candidates"]) > 0:
            candidate = result["candidates"][0]
            if "content" in candidate and "parts" in candidate["content"]:
                return candidate["content"]["parts"][0].get("text", "")

        raise click.ClickException("Unexpected response format from Gemini API")

    except requests.exceptions.Timeout:
        raise click.ClickException("Gemini API request timed out")
    except requests.exceptions.RequestException as e:
        raise click.ClickException(f"Gemini API error: {str(e)}")
    except Exception as e:
        raise click.ClickException(f"Error calling Gemini API: {str(e)}")


@click.command(name="batch-analyze")
@click.option("--status", type=click.Choice(["open", "resolved", "ignored"], case_sensitive=False), help="Filter by issue status")
@click.option("--level", type=click.Choice(["debug", "info", "warning", "error", "critical"], case_sensitive=False), help="Filter by error level")
@click.option("--tag", multiple=True, help="Filter by tags (can be specified multiple times)")
@click.option("--limit", type=int, default=20, help="Maximum number of errors to analyze (default: 20)")
@click.option("--model", default=None, help="Gemini model to use (overrides config)")
@click.option("--provider", default=None, type=click.Choice(["gemini", "ollama"], case_sensitive=False), help="AI provider to use (default: gemini)")
@click.option("--timeout", type=int, default=180, help="Timeout in seconds for the API request (default: 180)")
@click.option("--pager/--no-pager", default=True, help="Show output in a pager when long")
def batch_analyze(status, level, tag, limit, model, provider, timeout, pager):
    """Analyze multiple errors to find patterns and systemic issues.

    This command uses AI to analyze multiple error events at once, identifying:
    - Common patterns across errors
    - Potential root causes affecting multiple issues
    - Priority recommendations for fixes
    - Preventive measures

    Examples:
        crashvault batch-analyze --status open --limit 10
        crashvault batch-analyze --level error --level critical
        crashvault batch-analyze --tag database --limit 15
    """
    # Load issues and events
    issues = load_issues()
    events = load_events()

    # Filter events
    filtered_events = events

    if status:
        issue_ids = {issue["id"] for issue in issues if issue.get("status") == status}
        filtered_events = [e for e in filtered_events if e.get("issue_id") in issue_ids]

    if level:
        filtered_events = [e for e in filtered_events if e.get("level") == level]

    if tag:
        tag_set = set(tag)
        filtered_events = [e for e in filtered_events if tag_set.issubset(set(e.get("tags", [])))]

    if not filtered_events:
        raise click.ClickException("No events found matching the specified criteria")

    # Sort by timestamp (most recent first) and limit
    filtered_events.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    filtered_events = filtered_events[:limit]

    # Display summary
    console.print(f"\n[bold cyan]Batch Analysis Summary[/bold cyan]")
    console.print(f"Total events to analyze: {len(filtered_events)}")
    console.print(f"Filters applied: status={status or 'any'}, level={level or 'any'}, tags={list(tag) or 'none'}\n")

    # Prepare statistics
    from datetime import datetime
    timestamps = [e.get("timestamp") for e in filtered_events if e.get("timestamp")]
    time_range = "N/A"
    if timestamps:
        try:
            dates = [datetime.fromisoformat(ts.replace('Z', '+00:00')) for ts in timestamps]
            earliest = min(dates).strftime("%Y-%m-%d %H:%M")
            latest = max(dates).strftime("%Y-%m-%d %H:%M")
            time_range = f"{earliest} to {latest}"
        except Exception:
            pass

    level_counts = {}
    for e in filtered_events:
        lvl = e.get("level", "unknown")
        level_counts[lvl] = level_counts.get(lvl, 0) + 1

    level_distribution = ", ".join([f"{k}: {v}" for k, v in sorted(level_counts.items(), key=lambda x: -x[1])])

    # Count unique error messages
    unique_messages = set(e.get("message", "") for e in filtered_events)

    # Get AI configuration
    ai_config = get_ai_config()
    provider = provider or "gemini"  # Default to Gemini for batch analysis

    if provider == "gemini":
        gemini_config = ai_config.get("gemini", {})
        api_key = gemini_config.get("api_key", "")
        if not api_key:
            raise click.ClickException(
                "Gemini API key not configured. Set 'ai.gemini.api_key' in ~/.crashvault/config.json\n"
                "Get your API key from: https://makersuite.google.com/app/apikey"
            )
        model = model or gemini_config.get("model", "gemini-1.5-pro")

        # Prepare simplified error data for analysis
        error_summaries = []
        for e in filtered_events:
            error_summaries.append({
                "event_id": e.get("event_id"),
                "message": e.get("message"),
                "level": e.get("level"),
                "timestamp": e.get("timestamp"),
                "tags": e.get("tags", []),
                "stacktrace_preview": (e.get("stacktrace", "")[:500] + "...") if len(e.get("stacktrace", "")) > 500 else e.get("stacktrace", "")
            })

        # Build prompt
        prompt = BATCH_ANALYSIS_PROMPT.format(
            errors_json=json.dumps(error_summaries, indent=2),
            total_count=len(filtered_events),
            unique_count=len(unique_messages),
            time_range=time_range,
            level_distribution=level_distribution
        )

        # Call Gemini API
        console.print(f"[yellow]Calling Gemini API (model={model})...[/yellow]")
        output = _call_gemini_api(prompt, model, api_key, timeout)

    elif provider == "ollama":
        raise click.ClickException("Ollama provider not yet supported for batch-analyze. Use --provider=gemini")

    else:
        raise click.ClickException(f"Provider '{provider}' not supported. Use 'gemini'.")

    # Display output
    console.print("\n[bold green]Analysis Results:[/bold green]\n")
    if pager and len(output.splitlines()) > 25:
        click.echo_via_pager(output)
    else:
        click.echo(output)
