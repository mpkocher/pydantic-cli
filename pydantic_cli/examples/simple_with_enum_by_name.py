from enum import Enum, auto, IntEnum
from typing import Set

from pydantic_cli._compat import PYDANTIC_V2
if PYDANTIC_V2:
    from pydantic.v1 import BaseModel, Field
else:
    from pydantic import BaseModel
    from pydantic.fields import Field

from pydantic_cli import run_and_exit


class CastAbleEnum(Enum):
    """Example enum mixin that will cast enum from case-insensitive name"""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        try:
            lookup = {k.lower(): item.value for k, item in cls.__members__.items()}
            return lookup[v.lower()]
        except KeyError:
            raise ValueError(f"Invalid value {v}. {cls.cli_help()}")

    @classmethod
    def cli_help(cls) -> str:
        return f"Allowed={list(cls.__members__.keys())}"


class Mode(CastAbleEnum, IntEnum):
    alpha = auto()
    beta = auto()


class State(CastAbleEnum, str, Enum): # type: ignore[misc]
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    SUCCESSFUL = "SUCCESSFUL"


class Options(BaseModel):
    states: Set[State] = Field(
        ..., description=f"States to filter on. {State.cli_help()}"
    )
    mode: Mode = Field(..., description=f"Processing Mode to select. {Mode.cli_help()}")
    max_records: int = 100


def example_runner(opts: Options) -> int:
    print(f"Mock example running with {opts}")
    return 0


if __name__ == "__main__":
    run_and_exit(Options, example_runner, description=__doc__, version="0.1.0")
