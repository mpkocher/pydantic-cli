import typing
from typing import Annotated
from enum import Enum, auto, IntEnum
from typing import Set, TypeVar
import logging

from pydantic import (
    BaseModel,
    Field,
    BeforeValidator,
    AfterValidator,
    PlainValidator,
    PlainSerializer,
    WrapSerializer,
    GetCoreSchemaHandler,
)
from pydantic_core import CoreSchema, core_schema

from pydantic_cli import run_and_exit, Cmd

logger = logging.getLogger(__name__)

EnumType = TypeVar("EnumType", bound=Enum)


class CastAbleEnumMixin:
    """Example enum mixin that will cast enum from case-insensitive name.

    This is a bit of non-standard customization of an Enum.
    Any customization of coercing, or casting is going to potentially create friction points
    at the commandline level. Specifically, in the help description of the Field.

    This is written awkwardly to get around subclassing Enums
    """

    __members__: dict  # to make mypy happy

    #  FIXME Pydantic is a bit thorny or confusing here. Ideally, the validation
    #  should be wired into the enum. But it's not.
    #  Check https://docs.pydantic.dev/latest/migration/#defining-custom-types for more information.
    # @classmethod
    # def __get_pydantic_core_schema__(
    #         cls, source_type: typing.Any, handler: GetCoreSchemaHandler
    # ) -> CoreSchema:
    #     return core_schema.no_info_after_validator_function(cls, handler(str))

    @classmethod
    def validate(cls, v):
        try:
            lookup = {k.lower(): item.value for k, item in cls.__members__.items()}
            logger.debug(
                f"*** Got raw state '{v}'. Trying to cast/convert from {lookup}"
            )
            value = lookup[v.lower()]
            logger.debug(f"*** Successfully got {v}={value}")
            return value
        except KeyError:
            raise ValueError(f"Invalid value {v}. {cls.cli_help()}")

    @classmethod
    def cli_help(cls) -> str:
        return f"Allowed={list(cls.__members__.keys())}"


class Mode(CastAbleEnumMixin, IntEnum):
    alpha = auto()
    beta = auto()


class State(str, CastAbleEnumMixin, Enum):
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    SUCCESSFUL = "SUCCESSFUL"

    @classmethod
    def defaults(cls):
        return {cls.RUNNING, cls.SUCCESSFUL}


# I suspect there's a better way to do this.
STATE = Annotated[State, BeforeValidator(State.validate)]


class Options(Cmd):
    states: Annotated[
        Set[STATE],
        Field(
            description=f"States to filter on. {State.cli_help()}",
            default=State.defaults(),
        ),
    ]
    mode: Annotated[
        Mode,
        BeforeValidator(Mode.validate),
        Field(description=f"Processing Mode to select. {Mode.cli_help()}"),
    ]
    max_records: int = 100

    def run(self) -> None:
        print(f"Mock example running with {self}")


if __name__ == "__main__":
    run_and_exit(Options, description=__doc__, version="0.1.0")
