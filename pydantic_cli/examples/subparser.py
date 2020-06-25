"""
Example of Using a Subparser
"""
import sys
import logging
import typing as T
from pydantic import BaseModel, AnyUrl

from pydantic_cli.examples import ExampleConfigDefaults, LogLevel
from pydantic_cli import run_sp_and_exit, SubParser, DefaultConfig

log = logging.getLogger(__name__)


class AlphaOptions(BaseModel):
    class Config(DefaultConfig, ExampleConfigDefaults):
        CLI_EXTRA_OPTIONS = {
            "max_records": ("-m", "--max-records"),
            "input_file": ("-i",),
        }
        CLI_JSON_ENABLE = True

    input_file: str
    max_records: int = 10
    log_level: LogLevel = LogLevel.DEBUG


class BetaOptions(BaseModel):
    class Config(ExampleConfigDefaults):
        CLI_EXTRA_OPTIONS = {
            "url": ("-u", "--url"),
            "num_retries": ("-n", "--num-retries"),
            "input_file": ("-i",),
        }
        CLI_JSON_ENABLE = True

    url: AnyUrl
    num_retries: int = 3
    log_level: LogLevel = LogLevel.INFO


def prologue_handler(opts):
    """Define a general Prologue hook to setup logging for the application"""
    format_str = (
        "[%(levelname)s] %(asctime)s [%(name)s %(funcName)s %(lineno)d] %(message)s"
    )
    logging.basicConfig(
        level=opts.log_level.upper(), stream=sys.stdout, format=format_str
    )
    log.info(f"Set up log with level {opts.log_level} with opts:{opts}")
    log.debug(f"Running {__file__}")


def printer_runner(opts: T.Any):
    print(f"Mock example running with {opts}")
    return 0


def to_runner(sx):
    def example_runner(opts) -> int:
        print(f"Mock {sx} example running with {opts}")
        return 0

    return example_runner


def to_subparser_example():

    return {
        "alpha": SubParser(AlphaOptions, to_runner("Alpha"), "Alpha SP Description"),
        "beta": SubParser(BetaOptions, to_runner("Beta"), "Beta SP Description"),
    }


if __name__ == "__main__":
    run_sp_and_exit(
        to_subparser_example(),
        description=__doc__,
        version="0.1.0",
        prologue_handler=prologue_handler,
    )
