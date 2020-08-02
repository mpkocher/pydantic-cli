import logging
from typing import Optional, Tuple, Union
from pydantic import BaseModel

from pydantic_cli import run_and_exit, DefaultConfig, default_minimal_exception_handler
from pydantic_cli.examples import setup_logger


def _to_opt(sx: str) -> Tuple[str, str]:
    def f(x):
        return f"--{x}-{sx}"

    return f("enable"), f("disable")


class Options(BaseModel):
    input_file: str
    enable_alpha: bool
    enable_beta: bool = False
    enable_dragon: Union[str, int]
    # https: // pydantic - docs.helpmanual.io / usage / models /  # required-optional-fields
    enable_gamma: Optional[
        bool
    ]  # ... Don't use ellipsis in Pydantic with mypy. This is a really fundamental problem.
    enable_delta: Optional[bool] = None
    enable_epsilon: Optional[
        bool
    ] = True  # this a bit of a contradiction from the commandline perspective.

    class Config(DefaultConfig):
        CLI_EXTRA_OPTIONS = {
            "enable_alpha": _to_opt("alpha"),
            "enable_beta": ("--yes-beta", "--no-beta"),
            "enable_gamma": _to_opt("gamma"),
            "enable_delta": _to_opt("delta"),
            "enable_epsilon": _to_opt("epsilon"),
        }


def example_runner(opts: Options) -> int:
    print(f"Mock example running with {opts}")
    return 0


if __name__ == "__main__":
    logging.basicConfig(level="DEBUG")
    run_and_exit(
        Options,
        example_runner,
        exception_handler=default_minimal_exception_handler,
        prologue_handler=setup_logger,
    )
