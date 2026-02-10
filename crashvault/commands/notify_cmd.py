import click, json, subprocess, shutil, sys
from ..core import get_config_value, EVENTS_DIR


def _notify_win(title, message):
    try:
        import win10toast
        win10toast.ToastNotifier().show_toast(title, message, duration=5)
        return True
    except Exception:
        return False


def _notify_linux(title, message):
    if shutil.which("notify-send"):
        subprocess.run(["notify-send", title, message])
        return True
    return False


def _notify_macos(title, message):
    if shutil.which("osascript"):
        subprocess.run(["osascript", "-e", f'display notification "{message}" with title "{title}"'])
        return True
    return False


def send_notification(title, message):
    if sys.platform.startswith("win"):
        return _notify_win(title, message)
    if sys.platform == "darwin":
        return _notify_macos(title, message)
    return _notify_linux(title, message)


@click.command(name="notify")
@click.argument("event_id")
def notify(event_id):
    """Send a desktop notification for an event."""
    from ..rich_utils import get_console
    console = get_console()

    for p in EVENTS_DIR.glob("**/*.json"):
        if p.stem == event_id:
            ev = json.loads(p.read_text())
            title = f"Crashvault: #{ev.get('issue_id')} {ev.get('level','').upper()}"
            msg = ev.get("message", "")[:200]
            ok = send_notification(title, msg)
            if not ok:
                console.print("[warning]Notification not supported on this system.[/warning]")
            else:
                console.print("[success]Notification sent.[/success]")
            return
    raise click.ClickException("Event not found")


