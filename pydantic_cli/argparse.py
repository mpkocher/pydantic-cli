"""
Custom layer/utils for dealing with the every so thorny argparse
"""
import sys
import typing as T
from argparse import ArgumentParser, SUPPRESS, Action


class TerminalEagerCommand(Exception):
    """
    An "Eager" Action (e.g., --version, --help) has completed successfully

    This will be used as a Control structure to deal with the .exit()
    calls that are used on some Actions (e.g., Help, Version)
    """


class FailedExecutionException(Exception):
    def __init__(self, exit_code: int, message: str):
        self.exit_code = exit_code
        self.message = message
        super(FailedExecutionException, self).__init__(self.message)


class EagerHelpAction(Action):
    def __init__(self, option_strings, dest=SUPPRESS, default=SUPPRESS, help=None):
        super(EagerHelpAction, self).__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help,
        )

    def __call__(self, parser, namespace, values, option_string=None):
        parser.print_help()
        raise TerminalEagerCommand("Help completed running")


class EagerVersionAction(Action):
    def __init__(
        self,
        option_strings,
        version,
        dest=SUPPRESS,  # wtf does this do?
        default=SUPPRESS,
        help="show program's version number and exit",
    ):
        super(EagerVersionAction, self).__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help,
        )
        self.version = version

    def __call__(self, parser, namespace, values, option_string=None):
        version = self.version
        if version is None:
            version = parser.version
        formatter = parser._get_formatter()
        formatter.add_text(version)
        parser._print_message(formatter.format_help(), sys.stdout)
        raise TerminalEagerCommand("Version completed running")


class CustomArgumentParser(ArgumentParser):
    def exit(self, status: int = 0, message: T.Optional[str] = None) -> T.NoReturn:  # type: ignore
        # THIS IS NO longer used because of the custom Version and Help
        # This is a bit of an issue to return the exit code properly
        # log.debug(f"{self} Class:{self.__class__.__name__} called exit()")
        if status != 0:
            raise FailedExecutionException(
                status, f"Status ({status}) Failed to run command {message}"
            )


def _parser_add_help(p: CustomArgumentParser):
    p.add_argument(
        "--help", help="Print Help and Exit", action=EagerHelpAction, default=SUPPRESS
    )
    return p


def _parser_add_version(parser: ArgumentParser, version: str) -> ArgumentParser:
    parser.add_argument("--version", action=EagerVersionAction, version=version)
    return parser
