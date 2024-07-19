"""
Example that adds an option to emit shell autocomplete for bash/zsh
requires `shtab` to be installed.
"""

import sys
import logging

from pydantic import BaseModel, Field, ConfigDict

from pydantic_cli import __version__
from pydantic_cli import run_and_exit, CliConfig
from pydantic_cli.shell_completion import HAS_AUTOCOMPLETE_SUPPORT

log = logging.getLogger(__name__)


class Options(BaseModel):
    model_config = CliConfig(cli_shell_completion_enable=HAS_AUTOCOMPLETE_SUPPORT)

    input_file: str = Field(..., cli=("-i", "--input"))
    min_filter_score: float = Field(..., cli=("-f", "--filter-score"))
    max_records: int = Field(10, cli=("-m", "--max-records"))


def example_runner(opts: Options) -> int:
    log.info(
        f"pydantic_cli version={__version__} Mock example running with options {opts}"
    )
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    run_and_exit(Options, example_runner, description="Description", version="0.1.0")
