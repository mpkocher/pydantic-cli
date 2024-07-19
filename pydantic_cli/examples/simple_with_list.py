"""
# Simple Example of using Pydantic to generate a CLI

This example will generate a CLI tool with 2 **required** arguments
and can be called

```bash
my-tool --input_file file.fasta file2.fasta --max_records 10
```
"""

from typing import List, Set
from pydantic import BaseModel

from pydantic_cli import run_and_exit


class Options(BaseModel):
    input_file: list[str]
    filters: set[str]
    max_records: int


def example_runner(opts: Options) -> int:
    print(f"Mock example running with {opts}")
    return 0


if __name__ == "__main__":
    run_and_exit(Options, example_runner, description=__doc__, version="0.1.0")
