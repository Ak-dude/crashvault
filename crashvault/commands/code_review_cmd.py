"""Code review command using Gemini API."""
import click, json, subprocess
from pathlib import Path
from ..core import EVENTS_DIR, get_ai_config


REVIEW_FILE_PROMPT = """
You are a senior code reviewer. Review the following code and provide:
- Code quality assessment
- Potential bugs or issues
- Security concerns
- Performance considerations
- Best practice suggestions
- Specific improvement recommendations

FILE: {filename}
```
{code}
```
"""

REVIEW_ERROR_PROMPT = """
You are a senior code reviewer. Review the code related to this error and provide:
- Analysis of what caused the error
- Code quality issues that contributed to the error
- Suggestions to prevent similar errors
- Code improvements and best practices

ERROR EVENT:
{event_json}

CODE CONTEXT:
{code_context}
"""

REVIEW_DIFF_PROMPT = """
You are a senior code reviewer. Review the following git diff and provide:
- Assessment of the changes
- Potential bugs introduced
- Security implications
- Performance impact
- Best practice compliance
- Suggestions for improvement

GIT DIFF:
```
{diff}
```
"""


def _call_gemini_api(prompt, model, api_key, timeout):
    """Call Gemini API for code review."""
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
            "maxOutputTokens": 4096,
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


@click.command(name="code-review")
@click.option("--file", "file_path", type=click.Path(exists=True), help="Review a specific file")
@click.option("--error", "event_id", help="Review code related to an error event")
@click.option("--diff", is_flag=True, help="Review uncommitted git changes")
@click.option("--commit", help="Review a specific git commit")
@click.option("--model", default=None, help="Gemini model to use (overrides config)")
@click.option("--timeout", type=int, default=120, help="Timeout in seconds for the API request")
@click.option("--pager/--no-pager", default=True, help="Show output in a pager when long")
def code_review(file_path, event_id, diff, commit, model, timeout, pager):
    """Review code using Gemini API.

    This command supports multiple review modes:
    - Review a file: --file <path>
    - Review error-related code: --error <event_id>
    - Review git changes: --diff (uncommitted) or --commit <hash>

    Examples:
        crashvault code-review --file src/main.py
        crashvault code-review --error abc123
        crashvault code-review --diff
        crashvault code-review --commit HEAD
    """
    # Check that exactly one mode is specified
    modes = sum([bool(file_path), bool(event_id), bool(diff), bool(commit)])
    if modes == 0:
        raise click.ClickException("Please specify one review mode: --file, --error, --diff, or --commit")
    if modes > 1:
        raise click.ClickException("Please specify only one review mode at a time")

    # Get Gemini configuration
    ai_config = get_ai_config()
    gemini_config = ai_config.get("gemini", {})
    api_key = gemini_config.get("api_key", "")
    if not api_key:
        raise click.ClickException(
            "Gemini API key not configured. Set 'ai.gemini.api_key' in ~/.crashvault/config.json\n"
            "Get your API key from: https://makersuite.google.com/app/apikey"
        )
    model = model or gemini_config.get("model", "gemini-1.5-pro")

    # Build prompt based on mode
    if file_path:
        # Review file mode
        try:
            code = Path(file_path).read_text()
            prompt = REVIEW_FILE_PROMPT.format(filename=file_path, code=code)
            click.echo(f"Reviewing file: {file_path}", err=True)
        except Exception as e:
            raise click.ClickException(f"Error reading file: {str(e)}")

    elif event_id:
        # Review error mode
        event_file = None
        for p in EVENTS_DIR.glob("**/*.json"):
            if p.stem == event_id:
                event_file = p
                break
        if not event_file:
            raise click.ClickException(f"Event not found: {event_id}")

        try:
            ev = json.loads(event_file.read_text())

            # Extract code context from stacktrace
            from .diagnose_cmd import _extract_frames, _read_context
            frames = _extract_frames(ev.get("stacktrace", ""))
            contexts = []
            for path, line in frames[:3]:
                ctx = _read_context(path, line)
                if ctx:
                    contexts.append(f"{path} (line {line})\n{ctx}")
            code_context = "\n\n".join(contexts) if contexts else "(no source context)"

            prompt = REVIEW_ERROR_PROMPT.format(
                event_json=json.dumps(ev, indent=2),
                code_context=code_context
            )
            click.echo(f"Reviewing code related to error: {event_id}", err=True)
        except Exception as e:
            raise click.ClickException(f"Error processing event: {str(e)}")

    elif diff:
        # Review uncommitted changes
        try:
            result = subprocess.run(
                ["git", "diff", "--unified=5"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                raise click.ClickException("Failed to get git diff. Are you in a git repository?")

            diff_output = result.stdout
            if not diff_output.strip():
                raise click.ClickException("No uncommitted changes found")

            prompt = REVIEW_DIFF_PROMPT.format(diff=diff_output)
            click.echo("Reviewing uncommitted changes...", err=True)
        except subprocess.TimeoutExpired:
            raise click.ClickException("Git command timed out")
        except FileNotFoundError:
            raise click.ClickException("git command not found. Is git installed?")

    elif commit:
        # Review specific commit
        try:
            result = subprocess.run(
                ["git", "show", "--unified=5", commit],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                raise click.ClickException(f"Failed to get commit diff for: {commit}")

            diff_output = result.stdout
            prompt = REVIEW_DIFF_PROMPT.format(diff=diff_output)
            click.echo(f"Reviewing commit: {commit}", err=True)
        except subprocess.TimeoutExpired:
            raise click.ClickException("Git command timed out")
        except FileNotFoundError:
            raise click.ClickException("git command not found. Is git installed?")

    # Call Gemini API
    click.echo(f"Calling Gemini API (model={model})...", err=True)
    output = _call_gemini_api(prompt, model, api_key, timeout)

    # Display output
    if pager and len(output.splitlines()) > 25:
        click.echo_via_pager(output)
    else:
        click.echo(output)
