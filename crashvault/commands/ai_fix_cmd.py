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
def ai_fix(event_id, model):
    """Use local Ollama to analyze an error and suggest a fix."""
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
    
    if provider == "ollama":
        if not shutil.which("ollama"):
            raise click.ClickException("ollama CLI not found. Install Ollama or update PATH.")
        
        prompt = PROMPT_TMPL.format(event_json=json.dumps(ev, indent=2), code_context=code_context)
        try:
            # Pass prompt as text via stdin and request text output; use a timeout to avoid hanging
            result = subprocess.run(["ollama", "run", model], input=prompt, text=True, capture_output=True, timeout=60)
        except subprocess.TimeoutExpired:
            raise click.ClickException("Ollama request timed out")
        except FileNotFoundError:
            raise click.ClickException("ollama CLI not found. Install Ollama or update PATH.")
        except Exception as e:
            raise click.ClickException(str(e))
        if result.returncode != 0:
            err = result.stderr or result.stdout
            raise click.ClickException(err)
        click.echo(result.stdout)
    else:
        click.echo(f"AI provider '{provider}' not yet implemented. Please use 'ollama' for now.")
        click.echo("Edit ~/.crashvault/config.json to change AI settings.")


