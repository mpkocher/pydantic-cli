"""
Example using Pydantic-CLI to generate a custom CLI fields on a per field basis.
"""
import sys
import logging

from pydantic import BaseModel

from pydantic_cli import __version__ as Version
from pydantic_cli import run_and_exit
from pydantic_cli.examples import ConfigDefaults

log = logging.getLogger(__name__)


class Options(BaseModel):

    class Config(ConfigDefaults):
        CLI_EXTRA_OPTIONS = {'max_records': ('-m', )}

    input_file: str
    max_records: int = 10


def example_runner(opts: Options) -> int:
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    log.info(f"pydantic_cli version={Version} Mock example running with options {opts}")
    return 0


if __name__ == "__main__":
    run_and_exit(Options, example_runner, description="Description", version='0.1.0')
