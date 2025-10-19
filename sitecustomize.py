# Auto-import crashvault CleanError summarizer when running Python from this repository root.
# Placing this file at the project root ensures that when you run `python script.py`
# from the repo root the interpreter will import this and install the summarizer.
try:
    # Prefer the installed package if available, otherwise allow local import
    import crashvault.CleanError.summarize as _cv_summarize
except Exception:
    try:
        import sys
        sys.path.insert(0, '.')
        import crashvault.CleanError.summarize as _cv_summarize
    except Exception:
        # fail silently; we don't want to break startup if summarizer isn't importable
        _cv_summarize = None

# leaving a reference avoids linter warnings
__all__ = ['_cv_summarize']
