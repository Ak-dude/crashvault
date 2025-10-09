import click, json, time
from ..core import EVENTS_DIR


@click.command()
@click.option("--level", type=click.Choice(["debug","info","warning","error","critical"], case_sensitive=False))
@click.option("--tag", "tags", multiple=True)
@click.option("--text", default="")
@click.option("--interval", type=float, default=1.0, show_default=True, help="Polling interval seconds")
def tail(level, tags, text, interval):
    """Follow new events as they arrive."""
    seen = {p.stem for p in EVENTS_DIR.glob("**/*.json")}
    try:
        while True:
            new_files = [p for p in EVENTS_DIR.glob("**/*.json") if p.stem not in seen]
            if new_files:
                new_files.sort(key=lambda p: p.stat().st_mtime)
                for p in new_files:
                    seen.add(p.stem)
                    try:
                        ev = json.loads(p.read_text())
                    except Exception:
                        continue
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


