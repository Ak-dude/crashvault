import click

from .core import ensure_dirs, configure_logging
from .commands.add_cmd import add
from .commands.list_cmd import list_cmd as list
from .commands.show_cmd import show
from .commands.kill_cmd import kill
from .commands.resolve_cmd import resolve
from .commands.set_status_cmd import set_status
from .commands.reopen_cmd import reopen
from .commands.set_title_cmd import set_title
from .commands.purge_cmd import purge
from .commands.gc_cmd import gc
from .commands.search_cmd import search
from .commands.stats_cmd import stats
from .commands.export_cmd import export
from .commands.import_cmd import import_ as import_cmd
from .commands.tail_cmd import tail
from .commands.prune_cmd import prune
from .commands.events_cmd import events_cmd
from .commands.aliases import ls, rm, new, st, title_cmd, sh
from .commands.config_cmd import config_group
from .commands.misc_cmds import init, path
from .commands.docs import docs
from .commands.note_cmd import note
from .commands.report_cmd import report
from .commands.attach_cmd import attach
from .commands.wrap_cmd import wrap
from .commands.autolog_cmd import autolog
from .commands.diagnose_cmd import diagnose
from .commands.notify_cmd import notify
from .commands.test_cmd import test_cmd
from .commands.setup_cmd import setup_cmd
from .commands.generate_report_cmd import generate_report
from .commands.completion_cmd import completion
# from .commands.webhook_cmd import webhook
# from .commands.server_cmd import server


@click.group()
def cli():
    ensure_dirs()
    configure_logging()


# register config subgroup
cli.add_command(config_group, name="config")

# root commands
cli.add_command(add)
cli.add_command(list, name="list")
cli.add_command(show)
cli.add_command(kill)
cli.add_command(resolve)
cli.add_command(set_status, name="set-status")
cli.add_command(reopen)
cli.add_command(set_title, name="set-title")
cli.add_command(purge)
cli.add_command(gc)
cli.add_command(search)
cli.add_command(stats)
cli.add_command(export)
cli.add_command(import_cmd, name="import")
cli.add_command(tail)
cli.add_command(prune)
cli.add_command(events_cmd, name="events")
cli.add_command(init)
cli.add_command(path)
cli.add_command(note)
cli.add_command(report)
cli.add_command(attach)
cli.add_command(wrap)
cli.add_command(autolog)
cli.add_command(diagnose)
cli.add_command(notify)
cli.add_command(test_cmd, name="test")
cli.add_command(setup_cmd)
cli.add_command(generate_report)
cli.add_command(completion)

# webhook and server commands
# cli.add_command(webhook)
# cli.add_command(server)

cli.add_command(docs)

# aliases
cli.add_command(ls, name="ls")
cli.add_command(rm, name="rm")
cli.add_command(new, name="new")
cli.add_command(st, name="st")
cli.add_command(title_cmd, name="title")
cli.add_command(sh, name="sh")


