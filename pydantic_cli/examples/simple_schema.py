"""
Example of using pydantic_cli leveraging the Pydantic Field to add rich metadata
that will be communicated in the output of `--help`.

Note, that this leverages Pydantic's underlying validation mechanism. For example,
`max_records` must be > 0.
"""

from typing import Optional
from pydantic import BaseModel, Field

from pydantic_cli import run_and_exit, HAS_AUTOCOMPLETE_SUPPORT, CliConfig


class Options(BaseModel):
    model_config = CliConfig(
        frozen=True, cli_shell_completion_enable=HAS_AUTOCOMPLETE_SUPPORT
    )

    input_file: str = Field(
        ...,
        title="Input File",
        description="Path to the input file",
        # required=True, # this is implicitly set by ...
        cli=("-f", "--input-file"),
    )

    max_records: int = Field(
        123,
        title="Max Records",
        description="Max number of records",
        gt=0,
        cli=("-m",),
    )

    min_filter_score: float = Field(
        ...,
        title="Min Score",
        description="Minimum Score Filter that will be applied to the records",
        cli=("-s", "--min-filter-score"),
        gt=0,
    )

    max_filter_score: Optional[float] = Field(
        None,
        title="Max Score",
        description="Maximum Score Filter that will be applied to the records",
        gt=0,
        cli=("-S", "--max-filter-score"),
    )

    name: Optional[str] = Field(
        title="Filter Name",
        description="Name to Filter on.",
        cli=("-n", "--filter-name"),
    )


def example_runner(opts: Options) -> int:
    print(f"Mock example running with options {opts}")
    for x in (opts.input_file, opts.max_records, opts.min_filter_score, opts.name):
        print(f"{x} type={type(x)}")
    return 0


if __name__ == "__main__":
    run_and_exit(Options, example_runner, description=__doc__, version="0.1.0")
