"""
Example that adds an option to emit shell autocomplete for bash/zsh
requires `shtab` to be installed.
"""

import sys
import logging

from pydantic import Field

from pydantic_cli import __version__
from pydantic_cli import run_and_exit, CliConfig, Cmd
from pydantic_cli.shell_completion import HAS_AUTOCOMPLETE_SUPPORT

log = logging.getLogger(__name__)


class Options(Cmd):
    model_config = CliConfig(cli_shell_completion_enable=HAS_AUTOCOMPLETE_SUPPORT)

    input_file: str = Field(..., cli=("-i", "--input"))
    min_filter_score: float = Field(..., cli=("-f", "--filter-score"))
    max_records: int = Field(10, cli=("-m", "--max-records"))

    def run(self) -> None:
        log.info(
            f"pydantic_cli version={__version__} Mock example running with options {self}"
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    run_and_exit(Options, description="Description", version="0.1.0")
