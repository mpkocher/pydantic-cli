from enum import Enum, auto
from typing import Set
from pydantic import BaseModel

from pydantic_cli import run_and_exit, Cmd


class Mode(str, Enum):
    """Note that if you use `auto`, you must specify the enum
    using the int value (as a string).
    """

    alpha = auto()
    beta = auto()


class State(str, Enum):
    """Note, this is case sensitive when providing it from the commandline"""

    RUNNING = "RUNNING"
    FAILED = "FAILED"
    SUCCESSFUL = "SUCCESSFUL"


class Options(Cmd):
    states: Set[State]
    mode: Mode
    max_records: int = 100

    def run(self) -> None:
        print(f"Mock example running with {self}")


if __name__ == "__main__":
    run_and_exit(Options, description=__doc__, version="0.1.0")
