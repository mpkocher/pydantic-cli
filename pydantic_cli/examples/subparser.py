"""
Example of Using a Subparser

Demonstration of using two Pydantic data models to
build a subparser.

For example,

my-tool alpha --help
my-tool beta --help
"""
import sys
import logging
import typing as T
from pydantic import BaseModel, AnyUrl, Field

from pydantic_cli.examples import ExampleConfigDefaults, LogLevel, prologue_handler
from pydantic_cli import run_sp_and_exit, SubParser

log = logging.getLogger(__name__)


class CustomConfig(ExampleConfigDefaults):
    CLI_JSON_ENABLE = True


class AlphaOptions(BaseModel):
    class Config(CustomConfig):
        pass

    input_file: str = Field(..., extras={"cli": ("-i", "--input")})
    max_records: int = Field(10, extras={"cli": ("-m", "--max-records")})
    log_level: LogLevel = LogLevel.DEBUG


class BetaOptions(BaseModel):
    class Config(CustomConfig):
        pass

    url: AnyUrl = Field(..., extras={"cli": ("-u", "--url")})
    num_retries: int = Field(3, extras={"cli": ("-n", "--num-retries")})
    log_level: LogLevel = LogLevel.INFO


def to_func(sx):
    """Util func to create to custom mocked funcs that be used be each subparser"""

    def example_runner(opts) -> int:
        print(f"Mock {sx} example running with {opts}")
        return 0

    return example_runner


def to_subparser_example() -> T.Dict[str, SubParser]:
    """Simply create a dict of SubParser and pass the dict
    to `run_sp_and_exit` or `to_runner_sp`
    """
    return {
        "alpha": SubParser[AlphaOptions](
            AlphaOptions, to_func("Alpha"), "Alpha SP Description"
        ),
        "beta": SubParser[BetaOptions](
            BetaOptions, to_func("Beta"), "Beta SP Description"
        ),
    }


if __name__ == "__main__":
    run_sp_and_exit(
        to_subparser_example(),
        description=__doc__,
        version="0.1.0",
        prologue_handler=prologue_handler,
    )
