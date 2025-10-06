# crashvault.py
import click, json, os, uuid, hashlib, logging, platform
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path

ENV_ROOT = os.environ.get("CRASHVAULT_HOME")
ROOT = Path(ENV_ROOT) if ENV_ROOT else Path(os.path.expanduser("~/.crashvault"))
ISSUES_FILE = ROOT / "issues.json"
EVENTS_DIR = ROOT / "events"
LOGS_DIR = ROOT / "logs"
CONFIG_FILE = ROOT / "config.json"

def ensure_dirs():
    ROOT.mkdir(parents=True, exist_ok=True)
    EVENTS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    if not ISSUES_FILE.exists():
        ISSUES_FILE.write_text("[]")
    if not CONFIG_FILE.exists():
        _write_json_atomic(CONFIG_FILE, {"version": 1})

def configure_logging():
    """Configure a rotating file logger for internal tool diagnostics."""
    logger = logging.getLogger("crashvault")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    log_path = LOGS_DIR / "app.log"
    handler = RotatingFileHandler(log_path, maxBytes=1024 * 1024, backupCount=3)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def load_issues():
    ensure_dirs()
    with open(ISSUES_FILE, "r") as f:
        return json.load(f)

def save_issues(issues):
    _write_json_atomic(ISSUES_FILE, issues)

def load_events():
    ensure_dirs()
    events = []
    for f in EVENTS_DIR.glob("**/*.json"):
        try:
            ev = json.loads(f.read_text())
            events.append(ev)
        except Exception:
            continue
    return events

def _write_json_atomic(path: Path, data):
    """Write JSON atomically to avoid partial files on crash."""
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with open(tmp_path, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp_path, path)

def _event_path_for(event_id: str, ts: datetime) -> Path:
    day_dir = EVENTS_DIR / ts.strftime("%Y/%m/%d")
    day_dir.mkdir(parents=True, exist_ok=True)
    return day_dir / f"{event_id}.json"

def save_event(issue_id, message, stacktrace="", level="error", tags=None, context=None):
    event_id = str(uuid.uuid4())
    if tags is None:
        tags = []
    if context is None:
        context = {}
    ts = datetime.now(timezone.utc)
    data = {
        "event_id": event_id,
        "issue_id": issue_id,
        "message": message,
        "stacktrace": stacktrace,
        "timestamp": ts.isoformat().replace("+00:00", "Z"),
        "level": level.lower(),
        "tags": tags,
        "context": context,
        "host": platform.node(),
        "pid": os.getpid(),
    }
    _write_json_atomic(_event_path_for(event_id, ts), data)
    return event_id

@click.group()
def cli():
    ensure_dirs()
    configure_logging()

@cli.command()
def init():
    """Create the Crashvault data folder structure if missing."""
    ensure_dirs()
    click.echo(str(ROOT))

@cli.command()
def path():
    """Show the current Crashvault data path."""
    ensure_dirs()
    click.echo(str(ROOT))

def _load_config():
    ensure_dirs()
    try:
        return json.loads(CONFIG_FILE.read_text())
    except Exception:
        return {"version": 1}

def _save_config(cfg):
    _write_json_atomic(CONFIG_FILE, cfg)

@cli.group()
def config():
    """Manage Crashvault configuration."""
    ensure_dirs()

@config.command("get")
@click.argument("key")
def config_get(key):
    cfg = _load_config()
    click.echo(json.dumps(cfg.get(key)))

@config.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key, value):
    cfg = _load_config()
    # naive: try json parse, else store string
    try:
        cfg[key] = json.loads(value)
    except Exception:
        cfg[key] = value
    _save_config(cfg)
    click.echo("ok")

@cli.command(name="add")
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
        click.echo(f"Created new issue #{issue['id']}")
    context_dict = {}
    for kv in contexts:
        if "=" in kv:
            k, v = kv.split("=", 1)
            context_dict[k] = v
    ev_id = save_event(issue["id"], message, stack, level=level, tags=list(tags), context=context_dict)
    logger.info(f"event recorded | issue_id={issue['id']} | event_id={ev_id} | level={level}")
    click.echo(f"Event {ev_id} logged to issue #{issue['id']}")

@cli.command()
@click.option("--status", type=click.Choice(["open", "resolved", "ignored"], case_sensitive=False), help="Filter by status")
@click.option("--sort", type=click.Choice(["id", "title", "status", "created_at"], case_sensitive=False), default="id", show_default=True)
@click.option("--desc/--asc", default=False, show_default=True)
def list(status, sort, desc):
    issues = load_issues()
    if status:
        issues = [i for i in issues if i.get("status") == status]
    key = sort
    issues.sort(key=lambda i: i.get(key) if key != "id" else int(i.get("id", 0)), reverse=bool(desc))
    for i in issues:
        click.echo(f"#{i['id']} {i['title']} ({i['status']})")

@cli.command(name="ls")
@click.option("--status", type=click.Choice(["open", "resolved", "ignored"], case_sensitive=False))
def ls(status):
    """Alias for list with optional status filter."""
    ctx = click.get_current_context()
    ctx.invoke(list, status=status, sort="id", desc=False)

@cli.command()
@click.argument("issue_id", type=int)
def show(issue_id):
    issues = load_issues()
    issue = next((i for i in issues if i["id"] == issue_id), None)
    if not issue:
        click.echo("Issue not found")
        return
    click.echo(f"Issue #{issue['id']}: {issue['title']} ({issue['status']})")
    for f in EVENTS_DIR.glob("*.json"):
        ev = json.loads(f.read_text())
        if ev["issue_id"] == issue_id:
            click.echo(f"  - {ev['timestamp']} [{ev.get('level','').upper()}] {ev['message']}")
            if ev["stacktrace"]:
                click.echo(f"    Stack: {ev['stacktrace']}")
            if ev.get("tags"):
                click.echo(f"    Tags: {', '.join(ev['tags'])}")

@cli.command()
@click.confirmation_option(prompt="Are you sure you want to delete all logs?")
def kill():
    """Delete all issues and events (wipe logs)"""
    if ISSUES_FILE.exists():
        ISSUES_FILE.unlink()
    for f in EVENTS_DIR.glob("*.json"):
        f.unlink()
    click.echo("[red]All logs have been deleted![/red]")

@cli.command()
@click.argument("issue_id", type=int)
def resolve(issue_id):
    issues = load_issues()
    issue = next((i for i in issues if i["id"] == issue_id), None)
    if not issue:
        click.echo("Issue not found")
        return
    issue["status"] = "resolved"
    save_issues(issues)
    click.echo(f"Issue #{issue_id} marked resolved")

@cli.command("set-status")
@click.argument("issue_id", type=int)
@click.argument("status", type=click.Choice(["open", "resolved", "ignored"], case_sensitive=False))
def set_status(issue_id, status):
    """Set an issue's status (open|resolved|ignored)."""
    issues = load_issues()
    issue = next((i for i in issues if i["id"] == issue_id), None)
    if not issue:
        click.echo("Issue not found")
        return
    issue["status"] = status.lower()
    save_issues(issues)
    click.echo(f"Issue #{issue_id} status set to {status}")

@cli.command()
@click.argument("issue_id", type=int)
def reopen(issue_id):
    """Reopen a resolved/ignored issue."""
    issues = load_issues()
    issue = next((i for i in issues if i["id"] == issue_id), None)
    if not issue:
        click.echo("Issue not found")
        return
    issue["status"] = "open"
    save_issues(issues)
    click.echo(f"Issue #{issue_id} reopened")

@cli.command("set-title")
@click.argument("issue_id", type=int)
@click.argument("title")
def set_title(issue_id, title):
    """Rename an issue's title."""
    issues = load_issues()
    issue = next((i for i in issues if i["id"] == issue_id), None)
    if not issue:
        click.echo("Issue not found")
        return
    issue["title"] = title[:200]
    save_issues(issues)
    click.echo(f"Issue #{issue_id} title updated")

@cli.command()
@click.argument("issue_id", type=int)
@click.confirmation_option(prompt="Delete this issue and all of its events?")
def purge(issue_id):
    """Delete one issue and all related events."""
    issues = load_issues()
    before = len(issues)
    issues = [i for i in issues if i["id"] != issue_id]
    if len(issues) == before:
        click.echo("Issue not found")
        return
    save_issues(issues)
    removed_events = 0
    for f in EVENTS_DIR.glob("*.json"):
        try:
            ev = json.loads(f.read_text())
        except Exception:
            continue
        if ev.get("issue_id") == issue_id:
            try:
                f.unlink()
                removed_events += 1
            except Exception:
                pass
    click.echo(f"Purged issue #{issue_id} and {removed_events} event(s)")

@cli.command()
def gc():
    """Garbage collect orphaned events (without a valid issue)."""
    issues = load_issues()
    valid_ids = {i["id"] for i in issues}
    removed = 0
    for f in EVENTS_DIR.glob("*.json"):
        try:
            ev = json.loads(f.read_text())
        except Exception:
            try:
                f.unlink()
                removed += 1
            except Exception:
                pass
            continue
        if ev.get("issue_id") not in valid_ids:
            try:
                f.unlink()
                removed += 1
            except Exception:
                pass
    click.echo(f"Removed {removed} orphaned event file(s)")

@cli.command()
@click.option("--level", type=click.Choice(["debug","info","warning","error","critical"], case_sensitive=False), help="Filter by level")
@click.option("--tag", "tags", multiple=True, help="Filter by tag(s)")
@click.option("--text", default="", help="Search text in message")
def search(level, tags, text):
    """Search events with optional filters."""
    level = level.lower() if level else None
    count = 0
    for f in EVENTS_DIR.glob("*.json"):
        ev = json.loads(f.read_text())
        if level and ev.get("level") != level:
            continue
        if tags:
            etags = set(ev.get("tags", []))
            if not set(tags).issubset(etags):
                continue
        if text and text.lower() not in ev.get("message", "").lower():
            continue
        click.echo(f"{ev['timestamp']} [{ev.get('level','').upper()}] #{ev['issue_id']} {ev['message']}")
        count += 1
    click.echo(f"-- {count} event(s) matched --")

@cli.command()
def stats():
    """Show simple statistics about issues and events."""
    issues = load_issues()
    status_counts = {"open": 0, "resolved": 0}
    for i in issues:
        status_counts[i.get("status", "open")] = status_counts.get(i.get("status", "open"), 0) + 1
    level_counts = {}
    for f in EVENTS_DIR.glob("*.json"):
        ev = json.loads(f.read_text())
        lvl = ev.get("level", "unknown")
        level_counts[lvl] = level_counts.get(lvl, 0) + 1
    click.echo("Issues by status:")
    for k, v in status_counts.items():
        click.echo(f"  {k}: {v}")
    click.echo("Events by level:")
    for k, v in sorted(level_counts.items()):
        click.echo(f"  {k}: {v}")

@cli.command()
@click.option("--output", type=click.Path(dir_okay=False, writable=True, resolve_path=True), help="Output file (JSON). Defaults to stdout")
def export(output):
    """Export all issues and events to JSON."""
    payload = {
        "version": 1,
        "exported_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "issues": load_issues(),
        "events": load_events(),
    }
    data = json.dumps(payload, indent=2)
    if output:
        Path(output).write_text(data)
        click.echo(f"Exported to {output}")
    else:
        click.echo(data)

@cli.command(name="import")
@click.argument("input", type=click.Path(exists=True, dir_okay=False, readable=True, resolve_path=True))
@click.option("--mode", type=click.Choice(["merge", "replace"], case_sensitive=False), default="merge", show_default=True)
def import_(input, mode):
    """Import issues and events from an export JSON."""
    content = Path(input).read_text()
    incoming = json.loads(content)
    issues_in = incoming.get("issues", [])
    events_in = incoming.get("events", [])

    if mode.lower() == "replace":
        _write_json_atomic(ISSUES_FILE, [])
        for f in EVENTS_DIR.glob("*.json"):
            try:
                f.unlink()
            except Exception:
                pass

    existing = load_issues()
    fp_to_id = {i["fingerprint"]: i["id"] for i in existing}
    next_id = (max([i["id"] for i in existing]) + 1) if existing else 1

    # Merge issues by fingerprint
    for i in issues_in:
        fp = i.get("fingerprint")
        if fp in fp_to_id:
            # Update title/status but keep local id
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

    # Import events mapping by fingerprint
    imported = 0
    for ev in events_in:
        # We cannot know fingerprint from event directly, so match by issue_id via issues_in if present
        target_issue_id = ev.get("issue_id")
        mapped_issue_id = None
        if target_issue_id is not None and 0 <= target_issue_id - 1 < len(issues_in):
            src_issue = next((ix for ix in issues_in if ix.get("id") == target_issue_id), None)
            if src_issue:
                fp = src_issue.get("fingerprint")
                mapped_issue_id = fp_to_id.get(fp)
        if mapped_issue_id is None:
            # fallback: create/find by message fingerprint
            fp_msg = hashlib.sha1(ev.get("message", "").encode("utf-8")).hexdigest()[:8]
            mapped_issue_id = fp_to_id.get(fp_msg)
            if mapped_issue_id is None:
                # create a new issue for this event
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
        save_event(
            mapped_issue_id,
            ev.get("message", ""),
            stacktrace=ev.get("stacktrace", ""),
            level=ev.get("level", "error"),
            tags=ev.get("tags", []),
            context=ev.get("context", {}),
        )
        imported += 1
    click.echo(f"Imported {len(issues_in)} issue(s), {imported} event(s)")

@cli.command()
@click.option("--level", type=click.Choice(["debug","info","warning","error","critical"], case_sensitive=False))
@click.option("--tag", "tags", multiple=True)
@click.option("--text", default="")
@click.option("--interval", type=float, default=1.0, show_default=True, help="Polling interval seconds")
def tail(level, tags, text, interval):
    """Follow new events as they arrive."""
    import time
    seen = {p.stem for p in EVENTS_DIR.glob("*.json")}
    try:
        while True:
            new_files = [p for p in EVENTS_DIR.glob("*.json") if p.stem not in seen]
            if new_files:
                # Sort by mtime ascending
                new_files.sort(key=lambda p: p.stat().st_mtime)
                for p in new_files:
                    seen.add(p.stem)
                    try:
                        ev = json.loads(p.read_text())
                    except Exception:
                        continue
                    # reuse search filters
                    if level and ev.get("level") != level.lower():
                        continue
                    if tags:
                        etags = set(ev.get("tags", []))
                        if not set(tags).issubset(etags):
                            continue
                    if text and text.lower() not in ev.get("message", "").lower():
                        continue
                    click.echo(f"{ev['timestamp']} [{ev.get('level','').upper()}] #{ev['issue_id']} {ev['message']}")
            time.sleep(max(0.1, interval))
    except KeyboardInterrupt:
        click.echo("Stopped tailing.")

@cli.command(name="prune")
@click.option("--days", type=int, default=90, show_default=True, help="Remove events older than N days")
def prune(days):
    """Remove old events to save disk space."""
    cutoff = datetime.now(timezone.utc).timestamp() - (days * 86400)
    removed = 0
    for p in EVENTS_DIR.glob("**/*.json"):
        try:
            if p.stat().st_mtime < cutoff:
                p.unlink()
                removed += 1
        except Exception:
            continue
    click.echo(f"Pruned {removed} old event file(s)")

@cli.command(name="events")
@click.option("--issue", type=int, help="Only events for issue id")
@click.option("--limit", type=int, default=50, show_default=True)
@click.option("--offset", type=int, default=0, show_default=True)
def events_cmd(issue, limit, offset):
    """List events with optional pagination."""
    all_events = load_events()
    if issue is not None:
        all_events = [e for e in all_events if e.get("issue_id") == issue]
    all_events.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    page = all_events[offset: offset + limit]
    for ev in page:
        click.echo(f"{ev['timestamp']} [{ev.get('level','').upper()}] #{ev['issue_id']} {ev['message']}")
    click.echo(f"-- showing {len(page)} of {len(all_events)} --")

@cli.command(name="rm")
@click.argument("issue_id", type=int)
def rm(issue_id):
    """Alias for purge <issue_id>."""
    ctx = click.get_current_context()
    ctx.invoke(purge, issue_id=issue_id)

@cli.command(name="new")
@click.argument("message")
def new(message):
    """Alias for add <message>."""
    ctx = click.get_current_context()
    ctx.invoke(add, message=message, stack="", level="error", tags=(), contexts=())

@cli.command(name="st")
@click.argument("issue_id", type=int)
@click.argument("status", type=click.Choice(["open", "resolved", "ignored"], case_sensitive=False))
def st(issue_id, status):
    """Alias for set-status."""
    ctx = click.get_current_context()
    ctx.invoke(set_status, issue_id=issue_id, status=status)

@cli.command(name="title")
@click.argument("issue_id", type=int)
@click.argument("title")
def title_cmd(issue_id, title):
    """Alias for set-title."""
    ctx = click.get_current_context()
    ctx.invoke(set_title, issue_id=issue_id, title=title)

@cli.command(name="sh")
@click.argument("issue_id", type=int)
def sh(issue_id):
    """Alias for show."""
    ctx = click.get_current_context()
    ctx.invoke(show, issue_id=issue_id)

if __name__ == "__main__":
    cli()
