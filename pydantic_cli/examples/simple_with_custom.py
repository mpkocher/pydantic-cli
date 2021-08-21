"""
Example using pydantic-cli to generate a custom CLI fields on a per field basis
using the "quick" method.

The Pydantic Config can be used to override custom fields
For example, `CLI_EXTRA_OPTIONS` dict can be set to the
short and/or long argument form.

Set the value in the dict `-m` to add a "short" arg (the long default form will also be
automatically added).

CLI_EXTRA_OPTIONS = {"max_records": ('-m', )}

Or

CLI_EXTRA_OPTIONS = {"max_records": ('-m', '--max-records')}

"""
import sys
import logging
from typing import Union

from pydantic import BaseModel

from pydantic_cli import __version__
from pydantic_cli import run_and_exit, DefaultConfig
from pydantic_cli.examples import ExampleConfigDefaults

log = logging.getLogger(__name__)


class Options(BaseModel):
    class Config(ExampleConfigDefaults, DefaultConfig):
        CLI_EXTRA_OPTIONS = {
            "max_records": ("-m",),
            "min_filter_score": ("-f",),
            "input_file": ("-i",),
        }

    input_file: str
    min_filter_score: float
    max_records: int = 10
    alpha: Union[int, str] = 1


def example_runner(opts: Options) -> int:
    log.info(
        f"pydantic_cli version={__version__} Mock example running with options {opts}"
    )
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    run_and_exit(Options, example_runner, description="Description", version="0.1.0")
