import click, json, hashlib
from datetime import datetime, timezone
from pathlib import Path
from ..core import load_issues, save_issues
from ..core import ISSUES_FILE, EVENTS_DIR
from ..commands.add_cmd import add as add_cmd  # for structure reference
from ..core import event_path_for
import os, uuid, platform


@click.command(name="import")
@click.argument("input", type=click.Path(exists=True, dir_okay=False, readable=True, resolve_path=True))
@click.option("--mode", type=click.Choice(["merge", "replace"], case_sensitive=False), default="merge", show_default=True)
def import_(input, mode):
    """Import issues and events from an export JSON."""
    content = Path(input).read_text()
    incoming = json.loads(content)
    issues_in = incoming.get("issues", [])
    events_in = incoming.get("events", [])

    if mode.lower() == "replace":
        save_issues([])
        for f in EVENTS_DIR.glob("**/*.json"):
            try:
                f.unlink()
            except Exception:
                pass

    existing = load_issues()
    fp_to_id = {i["fingerprint"]: i["id"] for i in existing}
    next_id = (max([i["id"] for i in existing]) + 1) if existing else 1

    for i in issues_in:
        fp = i.get("fingerprint")
        if fp in fp_to_id:
            local_issue = next(ii for ii in existing if ii["id"] == fp_to_id[fp])
            local_issue["title"] = i.get("title", local_issue["title"])[:200]
            local_issue["status"] = i.get("status", local_issue.get("status", "open"))
        else:
            new_issue = {
                "id": next_id,
                "fingerprint": fp or hashlib.sha1(i.get("title", "").encode("utf-8")).hexdigest()[:8],
                "title": i.get("title", "")[:200],
                "status": i.get("status", "open"),
                "created_at": i.get("created_at", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")),
            }
            existing.append(new_issue)
            fp_to_id[new_issue["fingerprint"]] = new_issue["id"]
            next_id += 1
    save_issues(existing)

    imported = 0
    for ev in events_in:
        target_issue_id = ev.get("issue_id")
        mapped_issue_id = target_issue_id if any(i["id"] == target_issue_id for i in existing) else None
        if mapped_issue_id is None:
            fp_msg = hashlib.sha1(ev.get("message", "").encode("utf-8")).hexdigest()[:8]
            mapped_issue_id = fp_to_id.get(fp_msg)
            if mapped_issue_id is None:
                existing = load_issues()
                next_id = (max([i["id"] for i in existing]) + 1) if existing else 1
                new_issue = {
                    "id": next_id,
                    "fingerprint": fp_msg,
                    "title": ev.get("message", "")[:200],
                    "status": "open",
                    "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                }
                existing.append(new_issue)
                save_issues(existing)
                fp_to_id[fp_msg] = next_id
                mapped_issue_id = next_id
        event_id = str(uuid.uuid4())
        ts = datetime.now(timezone.utc)
        data = {
            "event_id": event_id,
            "issue_id": mapped_issue_id,
            "message": ev.get("message", ""),
            "stacktrace": ev.get("stacktrace", ""),
            "timestamp": ts.isoformat().replace("+00:00", "Z"),
            "level": ev.get("level", "error"),
            "tags": ev.get("tags", []),
            "context": ev.get("context", {}),
            "host": platform.node(),
            "pid": os.getpid(),
        }
        path = event_path_for(event_id, ts)
        tmp = path.with_suffix(path.suffix + ".tmp")
        with open(tmp, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, path)
        imported += 1
    from ..rich_utils import get_console
    console = get_console()
    console.print(f"[success]Imported {len(issues_in)} issue(s), {imported} event(s)[/success]")


