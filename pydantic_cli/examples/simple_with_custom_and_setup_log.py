"""
Example using Pydantic-CLI to generate a custom CLI fields on a per field basis
and setting up logging using the `prologue_handler`.

The `prologue_handler` provides a general mechanism to call
a setup hook with an instance of the Pydantic data model as the
argument to the function.
"""
import sys
import typing as T
import logging

from pydantic import BaseModel

from pydantic_cli import __version__
from pydantic_cli import run_and_exit
from pydantic_cli.examples import ExampleConfigDefaults, LogLevel

log = logging.getLogger(__name__)


class Options(BaseModel):
    class Config(ExampleConfigDefaults):
        CLI_EXTRA_OPTIONS = {
            "max_records": ("-m",),
            "log_level": ("-l",),
            "input_file": ("-i",),
        }

    input_file: str
    max_records: int = 10
    # this leverages Pydantic's fundamental understanding of Enums
    log_level: LogLevel = LogLevel.INFO


def prologue_handler(opts: Options):
    """Define a general Prologue hook to setup logging for the application"""
    format_str = (
        "[%(levelname)s] %(asctime)s [%(name)s %(funcName)s %(lineno)d] %(message)s"
    )
    logging.basicConfig(
        level=opts.log_level.upper(), stream=sys.stdout, format=format_str
    )
    log.info(f"Set up log with level {opts.log_level}")
    log.info(f"Running {__file__}")


def epilogue_handler(exit_code: int, run_time_sec: float):
    log.info(
        f"Completed running {__file__} with exit code {exit_code} in {run_time_sec} sec."
    )


def example_runner(opts: Options) -> int:
    log.info(
        f"pydantic_cli version={__version__} Mock example running with options {opts}"
    )
    return 0


if __name__ == "__main__":
    run_and_exit(
        Options,
        example_runner,
        description="Description",
        version="0.1.0",
        prologue_handler=prologue_handler,
        epilogue_handler=epilogue_handler,
    )
