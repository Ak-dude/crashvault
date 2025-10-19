"""CleanError: exception summarizer that replaces the default Python
traceback printer with a concise, human-friendly summary using rich.

Usage: import this module early (e.g. sitecustomize or manually) and
it will install itself as sys.excepthook. Call `install()` / `uninstall()`
to manage hook state programmatically.
"""

from __future__ import annotations

import sys
import traceback
from types import TracebackType
from typing import Optional, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.traceback import Traceback as RichTraceback

console = Console()


def _format_exception(exc_type, exc_value, tb: Optional[TracebackType]):
	"""Create a concise summary for the given exception info.

	Returns a tuple of (header_text, frames_table, code_blocks)
	where code_blocks is a list of (title, Syntax) that can be printed.
	"""
	header = f"[bold red]{exc_type.__name__}[/bold red]: {exc_value}"

	# Walk traceback and collect frames (limit to a few)
	frames = []
	extracted = traceback.extract_tb(tb) if tb is not None else []
	# show the last 6 frames (most relevant to error)
	for fr in extracted[-6:]:
		frames.append((fr.filename, fr.lineno, fr.name, fr.line))

	# Build a table of frames
	tbl = Table(show_header=True, header_style="bold cyan")
	tbl.add_column("File")
	tbl.add_column("Line", justify="right")
	tbl.add_column("Function")
	tbl.add_column("Source", overflow="fold")
	for fpath, lineno, func, src in frames:
		tbl.add_row(fpath, str(lineno), func, src or "")

	# Build code context blocks for the most relevant frame (last one)
	code_blocks = []
	if extracted:
		last = extracted[-1]
		try:
			with open(last.filename, 'r', encoding='utf-8') as fh:
				src_lines = fh.read().splitlines()
			# show context around the failing line
			start = max(0, last.lineno - 3 - 1)
			end = min(len(src_lines), last.lineno + 2)
			snippet = "\n".join(src_lines[start:end])
			syntax = Syntax(snippet, "python", line_numbers=True, start_line=start + 1, highlight_lines={last.lineno})
			title = f"{last.filename} — around line {last.lineno}"
			code_blocks.append((title, syntax))
		except Exception:
			# if source not available, skip
			pass

	return header, tbl, code_blocks


_original_excepthook = sys.excepthook


def _hook(exc_type, exc_value, tb):
	"""Custom excepthook: prints a short summary and a nice trace.

	Falls back to default hook for KeyboardInterrupt to preserve expected behavior.
	"""
	if exc_type is KeyboardInterrupt:
		# Use default to keep normal Ctrl-C semantics
		return _original_excepthook(exc_type, exc_value, tb)

	try:
		header, tbl, code_blocks = _format_exception(exc_type, exc_value, tb)
		console.rule("Exception summary")
		console.print(header)
		console.print(tbl)

		for title, syntax in code_blocks:
			console.print(Panel(syntax, title=title, border_style="magenta"))

		# Also print a short suggestion and the full rich traceback collapsed
		console.print("[bold]Suggestion:[/bold] inspect the top frame and local variables, or run with -X faulthandler for deeper inspection.")

		# A compact rich traceback (non-verbose) to let users expand if desired
		rt = RichTraceback.from_exception(exc_type, exc_value, tb, max_frames=10, show_locals=False)
		console.print(rt)
	except Exception:
		# If anything goes wrong while formatting, fallback to original
		_original_excepthook(exc_type, exc_value, tb)


def install():
	"""Install the CleanError excepthook globally."""
	global _original_excepthook
	if sys.excepthook is not _hook:
		_original_excepthook = sys.excepthook
		sys.excepthook = _hook


def uninstall():
	"""Restore the previous excepthook."""
	global _original_excepthook
	if sys.excepthook is _hook:
		sys.excepthook = _original_excepthook


# Auto-install when imported (explicit install() still available)
try:
	install()
except Exception:
	# keep failing import safe
	pass


__all__ = ["install", "uninstall"]