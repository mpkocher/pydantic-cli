"""
Example that adds an option to emit shell autocomplete for bash/zsh
requires `shtab` to be installed.
"""
import sys
import logging

from pydantic import BaseModel, Field

from pydantic_cli import __version__
from pydantic_cli import run_and_exit, DefaultConfig
from pydantic_cli.examples import ExampleConfigDefaults
from pydantic_cli.shell_completion import HAS_AUTOCOMPLETE_SUPPORT

log = logging.getLogger(__name__)


class Options(BaseModel):
    class Config(ExampleConfigDefaults, DefaultConfig):
        CLI_SHELL_COMPLETION_ENABLE = HAS_AUTOCOMPLETE_SUPPORT

    input_file: str = Field(..., extras={"cli": ("-i", "--input")})
    min_filter_score: float = Field(..., extras={"cli": ("-f", "--filter-score")})
    max_records: int = Field(10, extras={"cli": ("-m", "--max-records")})


def example_runner(opts: Options) -> int:
    log.info(
        f"pydantic_cli version={__version__} Mock example running with options {opts}"
    )
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    run_and_exit(Options, example_runner, description="Description", version="0.1.0")
