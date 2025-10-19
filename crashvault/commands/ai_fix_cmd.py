import click, json, subprocess, shutil
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


@click.command(name="ai-fix")
@click.argument("event_id")
@click.option("--model", default=None, help="Ollama model name (overrides config)")
@click.option("--method", type=click.Choice(["auto", "cli"], case_sensitive=False), default="auto", help="How to invoke Ollama: 'auto' (prefer CLI) or 'cli' (force CLI)")
@click.option("--timeout", type=int, default=60, help="Timeout in seconds for the Ollama request")
@click.option("--pager/--no-pager", default=True, help="Show AI output in a pager when long")
def ai_fix(event_id, model, method, timeout, pager):
    """Use local Ollama to analyze an error and suggest a fix.

    This command prefers the Ollama CLI when available. Use --method=cli to force
    CLI usage. If no CLI is found and method=auto, the command will explain how to
    configure an alternate provider instead of failing silently.
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
    model = model or ai_config.get("model", "qwen2.5-coder:7b")
    provider = ai_config.get("provider", "ollama")

    # Decide invocation method
    use_cli = False
    if method == "cli":
        use_cli = True
    else:  # auto
        use_cli = bool(shutil.which("ollama"))

    prompt = PROMPT_TMPL.format(event_json=json.dumps(ev, indent=2), code_context=code_context)

    if provider != "ollama":
        raise click.ClickException(f"AI provider '{provider}' not supported by this command. Set provider to 'ollama' in ~/.crashvault/config.json or use another tool.")

    if not use_cli:
        # No CLI available and we only support local Ollama via CLI for now
        raise click.ClickException(
            "Ollama CLI not found. Install Ollama (https://ollama.com) or ensure 'ollama' is on PATH.\n"
            "Alternatively, configure a supported AI provider in ~/.crashvault/config.json."
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
    if pager and len(out.splitlines()) > 25:
        click.echo_via_pager(out)
    else:
        click.echo(out)


