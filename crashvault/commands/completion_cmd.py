"""Shell completion script generation for bash, zsh, and fish."""

import click
import sys


_BASH_COMPLETION = '''# crashvault bash completion
# Add to ~/.bashrc or ~/.bash_completion:
#   eval "$(crashvault completion bash)"

_crashvault_completion() {
    local IFS=$'\\n'
    local response

    response=$(env COMP_WORDS="${COMP_WORDS[*]}" COMP_CWORD=$COMP_CWORD \\
        _CRASHVAULT_COMPLETE=bash_complete $1)

    for completion in $response; do
        IFS=',' read type value <<< "$completion"
        COMPREPLY+=("$value")
    done
    return 0
}

_crashvault_completion_setup() {
    complete -o default -F _crashvault_completion crashvault
}

_crashvault_completion_setup
'''

_ZSH_COMPLETION = '''#compdef crashvault
# crashvault zsh completion
# Add to ~/.zshrc:
#   eval "$(crashvault completion zsh)"

_crashvault() {
    local -a completions
    local -a completions_with_descriptions
    local -a response

    response=("${(@f)$(env COMP_WORDS="${words[*]}" COMP_CWORD=$((CURRENT-1)) \\
        _CRASHVAULT_COMPLETE=zsh_complete crashvault)}")

    for key descr in ${(kv)response}; do
        if [[ "$descr" == "_" ]]; then
            completions+=("$key")
        else
            completions_with_descriptions+=("$key":"$descr")
        fi
    done

    if [ -n "$completions_with_descriptions" ]; then
        _describe -V unsorted completions_with_descriptions -U
    fi

    if [ -n "$completions" ]; then
        compadd -U -V unsorted -a completions
    fi
}

if [[ $zsh_eval_context[-1] == loadautofun ]]; then
    _crashvault "$@"
else
    compdef _crashvault crashvault
fi
'''

_FISH_COMPLETION = '''# crashvault fish completion
# Add to ~/.config/fish/completions/crashvault.fish:
#   crashvault completion fish > ~/.config/fish/completions/crashvault.fish

function __crashvault_complete
    set -lx COMP_WORDS (commandline -cp)
    set -lx COMP_CWORD (math (count (commandline -cp)) - 1)
    set -lx _CRASHVAULT_COMPLETE fish_complete
    string split \\n -- (crashvault)
end

complete -c crashvault -f -a "(__crashvault_complete)"
'''

SHELLS = {
    'bash': _BASH_COMPLETION,
    'zsh': _ZSH_COMPLETION,
    'fish': _FISH_COMPLETION,
}


@click.command('completion')
@click.argument('shell', type=click.Choice(['bash', 'zsh', 'fish']), required=False)
@click.option('--install', is_flag=True, help='Install completion to the appropriate config file.')
def completion(shell, install):
    """Generate shell completion scripts.

    Usage:
      crashvault completion bash    # Print bash completion script
      crashvault completion zsh     # Print zsh completion script
      crashvault completion fish    # Print fish completion script

    Install directly:
      eval "$(crashvault completion bash)"
      eval "$(crashvault completion zsh)"
      crashvault completion fish > ~/.config/fish/completions/crashvault.fish
    """
    if shell is None:
        # Auto-detect shell
        import os
        current_shell = os.path.basename(os.environ.get('SHELL', ''))
        if current_shell in SHELLS:
            shell = current_shell
        else:
            click.echo("Could not detect shell. Please specify: bash, zsh, or fish", err=True)
            click.echo("\nUsage: crashvault completion [bash|zsh|fish]", err=True)
            sys.exit(1)

    script = SHELLS[shell]

    if install:
        _install_completion(shell, script)
    else:
        click.echo(script)


def _install_completion(shell, script):
    """Install completion script to the appropriate location."""
    import os
    from pathlib import Path

    home = Path.home()

    if shell == 'bash':
        target = home / '.bash_completion.d' / 'crashvault'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(script)
        click.echo(f"Installed bash completion to {target}")
        click.echo("Add to ~/.bashrc:  source ~/.bash_completion.d/crashvault")

    elif shell == 'zsh':
        target = home / '.zfunc' / '_crashvault'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(script)
        click.echo(f"Installed zsh completion to {target}")
        click.echo("Add to ~/.zshrc before compinit:  fpath+=~/.zfunc")

    elif shell == 'fish':
        target = home / '.config' / 'fish' / 'completions' / 'crashvault.fish'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(script)
        click.echo(f"Installed fish completion to {target}")
        click.echo("Fish will auto-load it on next shell start.")
