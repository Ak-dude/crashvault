"""Server commands for the CrashVault HTTP API."""

import click
import subprocess
import sys
import os


@click.group(name="server")
def server():
    """Manage the CrashVault HTTP server for receiving runtime errors."""
    pass


@server.command(name="start")
@click.option("--port", "-p", default=5678, help="Port to listen on", show_default=True)
@click.option("--host", "-h", default="0.0.0.0", help="Host to bind to", show_default=True)
@click.option("--background", "-b", is_flag=True, help="Run in background")
def start(port, host, background):
    """Start the HTTP server to receive runtime errors.

    The server listens for POST requests with error data:

        POST /api/v1/events
        {
            "message": "Error message",
            "stacktrace": "...",
            "level": "error",
            "tags": ["web", "frontend"],
            "context": {"user_id": "123"}
        }

    Example client integration (JavaScript):

        window.onerror = (msg, url, line, col, error) => {
            fetch('http://localhost:5678/api/v1/events', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    message: msg,
                    stacktrace: error?.stack,
                    source: url,
                    line: line
                })
            });
        };
    """
    from ..server import is_server_running, run_server

    pid = is_server_running()
    if pid:
        click.echo(f"Server already running (PID {pid})")
        return

    if background:
        # Start in background
        from ..core import ROOT

        log_file = ROOT / "logs" / "server.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)

        with open(log_file, "a") as log:
            proc = subprocess.Popen(
                [sys.executable, "-m", "crashvault.server", str(port), host],
                stdout=log,
                stderr=log,
                start_new_session=True,
            )
        click.echo(f"Server started in background (PID {proc.pid})")
        click.echo(f"Listening on http://{host}:{port}")
        click.echo(f"Log file: {log_file}")
    else:
        # Run in foreground
        run_server(port=port, host=host)


@server.command(name="stop")
def stop():
    """Stop the running CrashVault server."""
    from ..server import stop_server

    success, message = stop_server()
    click.echo(message)


@server.command(name="status")
def status():
    """Check if the server is running."""
    from ..server import is_server_running

    pid = is_server_running()
    if pid:
        click.echo(f"Server is running (PID {pid})")
    else:
        click.echo("Server is not running")


@server.command(name="logs")
@click.option("--lines", "-n", default=50, help="Number of lines to show")
@click.option("--follow", "-f", is_flag=True, help="Follow log output")
def logs(lines, follow):
    """View server logs."""
    from ..core import ROOT

    log_file = ROOT / "logs" / "server.log"

    if not log_file.exists():
        click.echo("No server logs found.")
        return

    if follow:
        # Use tail -f
        import subprocess
        try:
            subprocess.run(["tail", "-f", str(log_file)])
        except KeyboardInterrupt:
            pass
    else:
        # Show last N lines
        content = log_file.read_text()
        log_lines = content.strip().split("\n")
        for line in log_lines[-lines:]:
            click.echo(line)
