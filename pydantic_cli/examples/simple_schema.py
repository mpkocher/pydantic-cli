"""
Example of using pydantic_cli leveraging the Pydantic Field to add rich metadata
that will be communicated in the output of `--help`.

Note, that this leverages Pydantic's underlying validation mechanism. For example,
`max_records` must be > 0.
"""
from typing import Optional
from pydantic import BaseModel, Field

from pydantic_cli.examples import ExampleConfigDefaults
from pydantic_cli import run_and_exit, HAS_AUTOCOMPLETE_SUPPORT


class Options(BaseModel):
    class Config(ExampleConfigDefaults):
        CLI_SHELL_COMPLETION_ENABLE = HAS_AUTOCOMPLETE_SUPPORT

    input_file: str = Field(
        ...,
        title="Input File",
        description="Path to the input file",
        # required=True, # this is implicitly set by ...
        extras={"cli": ("-f", "--input-file")},
    )

    max_records: int = Field(
        123,
        title="Max Records",
        description="Max number of records",
        gt=0,
        extras={"cli": ("-m",)},
    )

    min_filter_score: float = Field(
        ...,
        title="Min Score",
        description="Minimum Score Filter that will be applied to the records",
        extras={"cli": ("-s",)},
        gt=0
        # or extras={'cli': ('-s', '--min-filter-score', )}
    )

    max_filter_score: Optional[float] = Field(
        None,
        title="Max Score",
        description="Maximum Score Filter that will be applied to the records",
        gt=0,
        extras={"cli": ("-S",)}
        # or extras={'cli': ('-S', '--min-filter-score', )}
    )


def example_runner(opts: Options) -> int:
    print(f"Mock example running with options {opts}")
    print((opts.input_file, type(opts.input_file)))
    print(opts.max_records, type(opts.max_records))
    print(opts.min_filter_score, type(opts.min_filter_score))
    return 0


if __name__ == "__main__":
    run_and_exit(Options, example_runner, description=__doc__, version="0.1.0")
