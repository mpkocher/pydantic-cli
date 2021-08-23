import logging
from enum import Enum
from typing import Optional, Union, Set
from pydantic import BaseModel
from pydantic.fields import Field

from pydantic_cli import run_and_exit, DefaultConfig, default_minimal_exception_handler
from pydantic_cli.examples import setup_logger


class State(str, Enum):
    """Note, this is case sensitive when providing it from the commandline"""

    RUNNING = "RUNNING"
    FAILED = "FAILED"
    SUCCESSFUL = "SUCCESSFUL"


class Options(BaseModel):
    class Config(DefaultConfig):
        pass

    # Simple Arg/Option can be added and a reasonable commandline "long" flag will be created.
    input_file: str

    # The description can be customized by using pydantic's Field.
    # Pydantic using `...` to semantically mean "required"
    input_file2: str = Field(..., description="Path to input HDF5 file")

    # Or customizing the CLI flag with a Tuple[str, str] of (short, long), or Tuple[str] of (long, )
    input_file3: str = Field(
        ..., description="Path to input H5 file", extras={"cli": ("-f", "--hdf5")}
    )

    # https://pydantic-docs.helpmanual.io/usage/models/#required-optional-fields
    # Pydantic has a bit of an odd model on how it treats Optional[T]
    # These end up being indistinguishable.
    outfile: Optional[str]
    fasta: Optional[str] = None
    # This is a "required" value that can be set to None, or str
    report_json: Optional[str] = Field(...)

    # Required Boolean options/flag can be added by
    alpha: bool

    # When specifying custom descriptions or flags as a pydantic Field, the flags should be specified as:
    # (short, long) or (long, ) and be the OPPOSITE of the default value provide
    beta_filter: bool = Field(
        False,
        description="Enable beta filter mode",
        extras={"cli": ("-b", "--beta-filter")},
    )

    # Again, note Pydantic will treat these as indistinguishable
    gamma: Optional[bool]
    delta: Optional[bool] = None

    # You need to set this to ... to declare it as "Required". The pydantic docs recommend using
    # Field(...) instead of ... to avoid issues with mypy.
    # pydantic-cli doesn't have a good mechanism for declaring this 3-state value of None, True, False.
    # using a boolean commandline flag (e.g., --enable-logging, or --disable-logging)
    zeta_mode: Optional[bool] = Field(
        ..., description="Enable/Disable Zeta mode to experimental filtering mode."
    )

    # this a bit of a contradiction from the commandline perspective. A "optional" value
    # with a default value. From a pydantic-cli view, the type should just be 'bool' because this 3-state
    # True, False, None is not well represented (i.e., can't set the value to None from the commandline)
    # Similar to the other Optional[bool] cases, the custom flag must be provided as a (--enable, --disable) format.
    epsilon: Optional[bool] = Field(
        False,
        description="Enable epsilon meta-analysis.",
        extras={"cli": ("--epsilon", "--disable-epsilon")},
    )

    states: Set[State]

    # The order of a Union is important. This doesn't really make any sense due to pydantic's core casting approach
    # This should be Union[int, str], but even with case,
    # there's an ambiguity. "1" will be cast to an int, which might not be the desired/expected results
    filter_mode: Union[str, int]


def example_runner(opts: Options) -> int:
    print(f"Mock example running with {opts}")
    return 0


if __name__ == "__main__":
    logging.basicConfig(level="DEBUG")
    run_and_exit(
        Options,
        example_runner,
        version="2.0.0",
        description="Example Commandline tool for demonstrating how custom fields/flags are communicated",
        exception_handler=default_minimal_exception_handler,
        prologue_handler=setup_logger,
    )
