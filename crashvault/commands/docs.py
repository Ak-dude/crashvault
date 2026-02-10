import click, shutil

@click.command(name="docs")
def docs():
    """Open the Crashvault documentation."""
    url = "https://github.com/arkattaholdings/crashvault?tab=readme-ov-file#crashvault"
    click.launch(url)