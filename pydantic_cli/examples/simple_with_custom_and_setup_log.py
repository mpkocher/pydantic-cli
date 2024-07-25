"""

Demonstrate a few key features of pydantic-cli

1. Leverage Python Enum within Pydantic Data models
2. Hooks: Add a pre-exec hook (prologue_handler) that can be used to setup logging
3. Hooks: Add a post-exec hook (epilogue_handler) that can be used to write a custom summary of the
output of the CLI tool


In this example, the `prologue_handler` sets up the application logging using logging.basicConfig
and the `epilogue_handler` will log the runtime and the exit code after the main execution function
is called.
"""

import sys
import logging

from pydantic import BaseModel, Field

from pydantic_cli import __version__, Cmd
from pydantic_cli import run_and_exit, CliConfig
from pydantic_cli.examples import LogLevel

log = logging.getLogger(__name__)


class Options(Cmd):
    model_config = CliConfig(frozen=True)

    input_file: str = Field(..., cli=("-i", "--input"))
    max_records: int = Field(10, cli=("-m", "--max-records"))
    # this leverages Pydantic's fundamental understanding of Enums
    log_level: LogLevel = LogLevel.INFO

    def run(self) -> None:
        log.info(
            f"pydantic_cli version={__version__} Mock example running with options {self}"
        )


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


if __name__ == "__main__":
    run_and_exit(
        Options,
        description=__doc__,
        version="0.1.0",
        prologue_handler=prologue_handler,
        epilogue_handler=epilogue_handler,
    )
