"""
# Simple Example of using Pydantic to generate a CLI

This example will generate a CLI tool with 2 **required** arguments
and can be called

```bash
my-tool --input_file file.fasta file2.fasta --max_records 10
```
"""

from pydantic_cli import run_and_exit, Cmd


class Options(Cmd):
    input_file: list[str]
    filters: set[str]
    max_records: int

    def run(self) -> None:
        print(f"Mock example running with {self}")


if __name__ == "__main__":
    run_and_exit(Options, description=__doc__, version="0.1.0")
