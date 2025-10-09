import click, subprocess, shutil


@click.command(name="test")
@click.option("--coverage/--no-coverage", default=True, show_default=True)
@click.option("--path", default=".", help="Path to tests (default: .)")
def test_cmd(coverage, path):
    """Run unit tests with pytest (and coverage if available)."""
    if not shutil.which("pytest"):
        raise click.ClickException("pytest not found. Please install it in your environment.")
    cmd = ["pytest", path]
    if coverage:
        # prefer coverage if installed; else use pytest --cov if available
        if shutil.which("coverage"):
            cmd = ["coverage", "run", "-m", "pytest", path]
        else:
            cmd = ["pytest", "--maxfail=1", "-q", path]
    result = subprocess.run(cmd)
    raise SystemExit(result.returncode)


