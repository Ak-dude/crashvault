import click, json, subprocess, shutil
from ..core import EVENTS_DIR, get_config_value


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

    model = model or get_config_value("ollama_model", "qwen2.5-coder:7b")
    if not shutil.which("ollama"):
        raise click.ClickException("ollama CLI not found. Install Ollama or update PATH.")

    prompt = PROMPT_TMPL.format(event_json=json.dumps(ev, indent=2), code_context=code_context)
    try:
        result = subprocess.run(["ollama", "run", model], input=prompt.encode("utf-8"), capture_output=True)
    except Exception as e:
        raise click.ClickException(str(e))
    if result.returncode != 0:
        raise click.ClickException(result.stderr.decode("utf-8", errors="ignore"))
    click.echo(result.stdout.decode("utf-8", errors="ignore"))


