"""
Loading of shtab to

Because of how argparse's parser.exit works, It's not
easy to reuse other actions. Specially the "eager" actions
which can at any point in time call parser.exit() which
doesn't work with how pydantic-cli is designed.
"""
import sys
from argparse import Action, ArgumentParser
from .argparse import TerminalEagerCommand

try:
    import shtab  # type: ignore
    from shtab import SUPPORTED_SHELLS

    HAS_AUTOCOMPLETE_SUPPORT = True
except ImportError:
    # let's just add these, then
    # create a runtime error instead of
    # failing to create choice option will no values
    SUPPORTED_SHELLS = ["zsh", "bash"]
    HAS_AUTOCOMPLETE_SUPPORT = False


class EmitShellCompletionAction(Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if not HAS_AUTOCOMPLETE_SUPPORT:
            raise ImportError("Unable to export to shell. shtab is not installed")

        if values in SUPPORTED_SHELLS:
            print(shtab.complete(parser, values))
            sys.stderr.write(f"Completed writing {values} shell output to stdout\n")
            raise TerminalEagerCommand

        raise ValueError(
            f"Unsupported shell type ({values}. Supported shells {SUPPORTED_SHELLS} "
        )


def add_shell_completion_arg(
    p: ArgumentParser, auto_complete_flag: str = "--emit-shell-completion"
) -> ArgumentParser:
    p.add_argument(
        auto_complete_flag,
        choices=list(SUPPORTED_SHELLS),
        default=None,
        help="Emit Shell Completion",
        action=EmitShellCompletionAction,
    )
    return p
