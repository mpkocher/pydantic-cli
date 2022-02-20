from enum import IntEnum
from typing import Set

from pydantic import BaseModel, Field

from pydantic_cli import run_and_exit


class Animal(IntEnum):
    """Access enum by name, pattern from
    https://github.com/samuelcolvin/pydantic/issues/598#issuecomment-503032706"""

    CAT = 1
    DOG = 2

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        try:
            return cls.__members__[v]
        except KeyError:
            raise ValueError('invalid value')


class Options(BaseModel):
    favorite_animal: Animal = Field(..., use_enum_names=True)
    animals: Set[Animal] = Field(..., use_enum_names=True)


def example_runner(opts: Options) -> int:
    print(f"Mock example running with {opts}")
    return 0


if __name__ == "__main__":
    run_and_exit(Options, example_runner, description=__doc__, version="0.1.0")
