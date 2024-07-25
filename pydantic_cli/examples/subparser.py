"""
Example of Using a Subparser

Demonstration of using two Pydantic data models to
build a subparser.

For example,

my-tool alpha --help
my-tool beta --help
"""

import logging
from typing import Mapping

from pydantic import AnyUrl, Field

from pydantic_cli.examples import LogLevel, prologue_handler
from pydantic_cli import Cmd, run_and_exit, CliConfig

log = logging.getLogger(__name__)

CLI_CONFIG = CliConfig(cli_json_enable=True, frozen=True)


class AlphaOptions(Cmd):
    model_config = CLI_CONFIG

    input_file: str = Field(..., cli=("-i", "--input"))
    max_records: int = Field(10, cli=("-m", "--max-records"))
    log_level: LogLevel = LogLevel.DEBUG

    def run(self) -> None:
        print(f"Mock example running with {self}")


class BetaOptions(Cmd):
    model_config = CLI_CONFIG

    url: AnyUrl = Field(..., cli=("-u", "--url"))
    num_retries: int = Field(3, cli=("-n", "--num-retries"))
    log_level: LogLevel = LogLevel.INFO

    def run(self) -> None:
        print(f"Mock example running with {self}")


CMDS: Mapping[str, type[Cmd]] = {"alpha": AlphaOptions, "beta": BetaOptions}

if __name__ == "__main__":
    run_and_exit(
        CMDS,
        description=__doc__,
        version="0.1.0",
        prologue_handler=prologue_handler,
    )
