"""
Simple Example of using Pydantic to generate a CLI

This example will generate a CLI tool with 1 required argument and one optional boolean arg.

Note the optional boolean value must be supplied as `--run_training False`
"""

from pydantic_cli import run_and_exit, Cmd


class Options(Cmd):
    input_file: str
    run_training: bool = True
    dry_run: bool = False

    def run(self) -> None:
        print(f"Mock example running with {self}")


if __name__ == "__main__":
    run_and_exit(Options, description=__doc__, version="0.1.0")
