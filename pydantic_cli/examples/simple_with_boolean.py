"""
Simple Example of using Pydantic to generate a CLI

This example will generate a CLI tool with 1 positional argument and one optional boolean arg
"""
from pydantic import BaseModel

from pydantic_cli import run_and_exit


class Options(BaseModel):
    input_file: str
    run_training: bool = False


def example_runner(opts: Options) -> int:
    print(f"Mock example running with {opts}")
    return 0


if __name__ == "__main__":
    run_and_exit(Options, example_runner, description=__doc__, version="0.1.0")
