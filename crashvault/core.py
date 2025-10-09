from pathlib import Path
import os, json, logging, platform
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler

ENV_ROOT = os.environ.get("CRASHVAULT_HOME")
ROOT = Path(ENV_ROOT) if ENV_ROOT else Path(os.path.expanduser("~/.crashvault"))
ISSUES_FILE = ROOT / "issues.json"
EVENTS_DIR = ROOT / "events"
LOGS_DIR = ROOT / "logs"
CONFIG_FILE = ROOT / "config.json"
ATTACH_DIR = ROOT / "attachments"


def ensure_dirs():
    ROOT.mkdir(parents=True, exist_ok=True)
    EVENTS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    ATTACH_DIR.mkdir(parents=True, exist_ok=True)
    if not ISSUES_FILE.exists():
        ISSUES_FILE.write_text("[]")
    if not CONFIG_FILE.exists():
        _write_json_atomic(CONFIG_FILE, {"version": 1})


def configure_logging():
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


def _write_json_atomic(path: Path, data):
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with open(tmp_path, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp_path, path)


def _event_day_dir(ts: datetime) -> Path:
    day_dir = EVENTS_DIR / ts.strftime("%Y/%m/%d")
    day_dir.mkdir(parents=True, exist_ok=True)
    return day_dir


def event_path_for(event_id: str, ts: datetime) -> Path:
    return _event_day_dir(ts) / f"{event_id}.json"


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


def load_config():
    ensure_dirs()
    try:
        return json.loads(CONFIG_FILE.read_text())
    except Exception:
        return {"version": 1}


def save_config(cfg):
    _write_json_atomic(CONFIG_FILE, cfg)
