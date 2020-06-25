"""
Example demonstrating how to configure JSON configuration file loading
"""
import logging
from pydantic import BaseModel
from pydantic_cli import run_and_exit, DefaultConfig
from pydantic_cli.examples import epilogue_handler, prologue_handler

log = logging.getLogger(__name__)


class Opts(BaseModel):
    class Config(DefaultConfig):
        CLI_JSON_KEY = "json-config"
        CLI_JSON_ENABLE = True

    hdf_file: str
    max_records: int = 10
    min_filter_score: float
    alpha: float
    beta: float


def runner(opts: Opts) -> int:
    print(f"Running with opts:{opts}")
    return 0


if __name__ == "__main__":
    run_and_exit(
        Opts,
        runner,
        description="My Tool Description",
        version="0.1.0",
        prologue_handler=prologue_handler,
        epilogue_handler=epilogue_handler,
    )
