from rich.console import Console
from rich.theme import Theme

_theme = Theme({
    "success": "bold green",
    "warning": "bold yellow",
    "error": "bold red",
    "highlight": "bold cyan",
    "muted": "dim",
})

_console = Console(theme=_theme)


def get_console() -> Console:
    return _console
