"""
Simple Example of using Pydantic to generate a CLI

This example will generate a CLI tool with 1 required argument and one optional boolean arg.

Note the optional boolean value must be supplied as `--run_training False`
"""

from pydantic import BaseModel, Field

from pydantic_cli import run_and_exit, CliConfig


class Options(BaseModel):
    model_config = CliConfig(frozen=True)

    input_file: str
    run_training: bool = Field(default=False, cli=("-t", "--run-training"))
    dry_run: bool = Field(default=False, cli=("-r", "--dry-run"))


def example_runner(opts: Options) -> int:
    print(f"Mock example running with {opts}")
    return 0


if __name__ == "__main__":
    run_and_exit(Options, example_runner, description=__doc__, version="0.1.0")
