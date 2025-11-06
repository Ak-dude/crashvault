import click, json, subprocess, shutil, os
from ..core import EVENTS_DIR, get_ai_config


PROMPT_TMPL = """
You are a senior engineer. Analyze the following error and code context, and propose a minimal fix. Respond with:
- Root cause (1-2 lines)
- Suggested fix (1-3 steps)
- Example patch snippet

ERROR EVENT:
{event_json}

CODE CONTEXT:
{code_context}
"""


def _call_gemini_api(prompt, model, api_key, timeout):
    """Call Gemini API for AI analysis."""
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
            "maxOutputTokens": 2048,
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


@click.command(name="ai-fix")
@click.argument("event_id")
@click.option("--model", default=None, help="AI model name (overrides config)")
@click.option("--provider", default=None, type=click.Choice(["ollama", "gemini"], case_sensitive=False), help="AI provider to use (overrides config)")
@click.option("--method", type=click.Choice(["auto", "cli"], case_sensitive=False), default="auto", help="How to invoke Ollama: 'auto' (prefer CLI) or 'cli' (force CLI)")
@click.option("--timeout", type=int, default=60, help="Timeout in seconds for the AI request")
@click.option("--pager/--no-pager", default=True, help="Show AI output in a pager when long")
def ai_fix(event_id, model, provider, method, timeout, pager):
    """Use AI (Ollama or Gemini) to analyze an error and suggest a fix.

    This command supports multiple AI providers:
    - Ollama: Local AI via CLI (default)
    - Gemini: Google's Gemini API

    Use --provider to override the configured provider in ~/.crashvault/config.json
    """
    event_file = None
    for p in EVENTS_DIR.glob("**/*.json"):
        if p.stem == event_id:
            event_file = p
            break
    if not event_file:
        raise click.ClickException("Event not found")
    ev = json.loads(event_file.read_text())

    # reuse diagnose parsing for context
    from .diagnose_cmd import _extract_frames, _read_context
    frames = _extract_frames(ev.get("stacktrace", ""))
    contexts = []
    for path, line in frames[:3]:
        ctx = _read_context(path, line)
        if ctx:
            contexts.append(f"{path} (line {line})\n{ctx}")
    code_context = "\n\n".join(contexts) if contexts else "(no source context)"

    ai_config = get_ai_config()
    provider = provider or ai_config.get("provider", "ollama")

    prompt = PROMPT_TMPL.format(event_json=json.dumps(ev, indent=2), code_context=code_context)

    # Handle different providers
    if provider == "gemini":
        gemini_config = ai_config.get("gemini", {})
        api_key = gemini_config.get("api_key", "")
        if not api_key:
            raise click.ClickException(
                "Gemini API key not configured. Set 'ai.gemini.api_key' in ~/.crashvault/config.json\n"
                "Get your API key from: https://makersuite.google.com/app/apikey"
            )
        model = model or gemini_config.get("model", "gemini-1.5-pro")
        click.echo(f"Calling Gemini API (model={model})...", err=True)
        out = _call_gemini_api(prompt, model, api_key, timeout)

    elif provider == "ollama":
        model = model or ai_config.get("model", "qwen2.5-coder:7b")

        # Decide invocation method
        use_cli = False
        if method == "cli":
            use_cli = True
        else:  # auto
            use_cli = bool(shutil.which("ollama"))

        if not use_cli:
            raise click.ClickException(
                "Ollama CLI not found. Install Ollama (https://ollama.com) or ensure 'ollama' is on PATH.\n"
                "Alternatively, use --provider=gemini or configure Gemini in ~/.crashvault/config.json."
            )

        # Invoke Ollama CLI
        try:
            click.echo(f"Calling Ollama CLI (model={model})...", err=True)
            result = subprocess.run(["ollama", "run", model], input=prompt, text=True, capture_output=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            raise click.ClickException("Ollama request timed out")
        except FileNotFoundError:
            raise click.ClickException("ollama CLI not found. Install Ollama or update PATH.")
        except Exception as e:
            raise click.ClickException(str(e))

        if result.returncode != 0:
            err = result.stderr or result.stdout or "(no output)"
            raise click.ClickException(f"Ollama CLI returned an error:\n{err}")

        out = result.stdout or ""

    else:
        raise click.ClickException(f"AI provider '{provider}' not supported. Use 'ollama' or 'gemini'.")

    # Display output
    if pager and len(out.splitlines()) > 25:
        click.echo_via_pager(out)
    else:
        click.echo(out)


