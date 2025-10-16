import sys
import logging
from typing import Union, Literal

from pydantic import Field

from pydantic_cli import (
    __version__,
    default_exception_handler_verbose,
    default_exception_handler,
)
from pydantic_cli import run_and_exit, CliConfig, Cmd

log = logging.getLogger(__name__)


class Options(Cmd):
    model_config = CliConfig(frozen=True)

    input_file: str = Field(..., cli=("-i", "--input"))
    max_records: int = Field(10, cli=("-m", "--max-records"))
    min_filter_score: float = Field(..., cli=("-f", "--filter-score"))
    alpha: Union[int, str] = 1
    beta: Literal["a", "b"] = "a"

    def run(self) -> None:
        log.info(
            f"pydantic_cli version={__version__} Mock example running with options {self}"
        )
        # for testing purposes
        if self.max_records <= 0:
            raise ValueError("max_records must be a positive integer")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    run_and_exit(
        Options,
        description="Description",
        version="0.1.0",
        exception_handler=default_exception_handler,
    )
