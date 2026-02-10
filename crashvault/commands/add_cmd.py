import click, hashlib, logging
from datetime import datetime, timezone

from ..core import load_issues, save_issues, event_path_for
import json, os, uuid, platform


@click.command(name="add")
@click.argument("message")
@click.option("--stack", default="", help="Stack trace")
@click.option("--level", type=click.Choice(["debug","info","warning","error","critical"], case_sensitive=False), default="error", show_default=True, help="Severity level")
@click.option("--tag", "tags", multiple=True, help="Tag(s) for this event; can repeat")
@click.option("--context", "contexts", multiple=True, help="Context key=value; can repeat")
def add(message, stack, level, tags, contexts):
    logger = logging.getLogger("crashvault")
    issues = load_issues()
    fp = hashlib.sha1(message.encode("utf-8")).hexdigest()[:8]
    issue = next((i for i in issues if i["fingerprint"] == fp), None)
    if not issue:
        issue = {
            "id": len(issues)+1,
            "fingerprint": fp,
            "title": message[:80],
            "status": "open",
            "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        }
        issues.append(issue)
        save_issues(issues)
        from ..rich_utils import get_console
        console = get_console()
        console.print(f"[success]Created new issue[/success] [highlight]#{issue['id']}[/highlight]")
    context_dict = {}
    for kv in contexts:
        if "=" in kv:
            k, v = kv.split("=", 1)
            context_dict[k] = v
    event_id = str(uuid.uuid4())
    ts = datetime.now(timezone.utc)
    data = {
        "event_id": event_id,
        "issue_id": issue["id"],
        "message": message,
        "stacktrace": stack,
        "timestamp": ts.isoformat().replace("+00:00", "Z"),
        "level": level.lower(),
        "tags": list(tags),
        "context": context_dict,
        "host": platform.node(),
        "pid": os.getpid(),
    }
    path = event_path_for(event_id, ts)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)
    logger.info(f"event recorded | issue_id={issue['id']} | event_id={event_id} | level={level}")
    from ..rich_utils import get_console
    console = get_console()
    console.print(f"[success]Event {event_id} logged to issue[/success] [highlight]#{issue['id']}[/highlight]")

    # Dispatch webhooks
    try:
        from ..webhooks.dispatcher import dispatch_webhooks
        dispatch_webhooks(data)
    except Exception:
        pass  # Don't fail the command if webhooks fail


