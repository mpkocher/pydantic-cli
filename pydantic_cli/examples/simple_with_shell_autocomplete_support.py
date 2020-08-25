"""
Example that adds an option to emit shell autocomplete for bash/zsh
requires `shtab` to be installed.
"""
import sys
import logging

from pydantic import BaseModel

from pydantic_cli import __version__
from pydantic_cli import run_and_exit, DefaultConfig
from pydantic_cli.examples import ExampleConfigDefaults
from pydantic_cli.shell_completion import HAS_AUTOCOMPLETE_SUPPORT

log = logging.getLogger(__name__)


class Options(BaseModel):
    class Config(ExampleConfigDefaults, DefaultConfig):
        CLI_EXTRA_OPTIONS = {
            "max_records": ("-m",),
            "min_filter_score": ("-f",),
            "input_file": ("-i",),
        }
        CLI_SHELL_COMPLETION_ENABLE = HAS_AUTOCOMPLETE_SUPPORT

    input_file: str
    min_filter_score: float
    max_records: int = 10


def example_runner(opts: Options) -> int:
    log.info(
        f"pydantic_cli version={__version__} Mock example running with options {opts}"
    )
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    run_and_exit(Options, example_runner, description="Description", version="0.1.0")
