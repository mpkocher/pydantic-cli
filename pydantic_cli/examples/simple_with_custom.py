import sys
import logging
from typing import Union, List

from pydantic import BaseModel, Field

from pydantic_cli import __version__
from pydantic_cli import run_and_exit, CliConfig

log = logging.getLogger(__name__)


class Options(BaseModel):
    model_config = CliConfig(frozen=True)

    input_file: str = Field(..., cli=("-i", "--input"))
    max_records: int = Field(10, cli=("-m", "--max-records"))
    min_filter_score: float = Field(..., cli=("-f", "--filter-score"))
    alpha: Union[int, str] = 1
    # values: List[str] = ["a", "b", "c"]


def example_runner(opts: Options) -> int:
    log.info(
        f"pydantic_cli version={__version__} Mock example running with options {opts}"
    )
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    run_and_exit(Options, example_runner, description="Description", version="0.1.0")
