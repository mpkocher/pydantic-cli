# Pydantic Commandline Tool Interface

Turn Pydantic defined Data Models into CLI Tools!


## Quick Start


To create a commandline tool that takes an input file and max number of records to process as positional arguments:

```bash
my-tool /path/to/file.txt 1234
```

Would use the following:

```python
import sys

from pydantic import BaseModel
from pydantic_cli import run_and_exit, to_runner

class MinOptions(BaseModel):
    input_file: str
    max_records: int = 10


def example_runner(opts: MinOptions) -> int:
    print(f"Mock example running with options {opts}")
    return 0

if __name__ == '__main__':
    sys.exit(to_runner(MinOptions, example_runner, version='0.1.0')(sys.argv[1:]))

```

Or to implicitly use `sys.argv[1:]`, call can leverage `run_and_exit` (`to_runner` is also useful for testing).

```python
if __name__ == '__main__':
    run_and_exit(MinOptions, example_runner, description="My Tool Description", version='0.1.0')

```

The `--help` is quite minimal (due to the lack of metadata), however, verbosely named arguments can often be good enough to communicate the intent of the commandline interface.


To enable more control (e.g., max number of records is `-m 1234`) over the fields in the data model are converted to a CLI, there are two approaches. 

- The first is the "quick" method that is a minor change to the `Config` of the Pydantic Data model. 
- The second method the "schema" method which leverages the `Schema` model in Pydantic 


### Quick Model

We're going to change the usage from `my-tool /path/to/file.txt 1234` to `my-tool /path/to/file.txt --max-records 1234` (or `-m 1234`).

This only requires adding  `CLI_EXTRA_OPTIONS` to the Pydantic `Config`.

```python
from pydantic import BaseModel

class MinOptions(BaseModel):

    class Config:
        CLI_EXTRA_OPTIONS = {'max_records': ('-m', '--max-records')}

    input_file: str
    max_records: int = 10

```


### Schema Approach


```python
from pydantic import BaseModel, Schema


class Options(BaseModel):

    class Config:
        validate_all = True
        validate_assignment = True

    input_file: str = Schema(
        ...,
        title="Input File",
        description="Path to the input file",
        required=True,
        extras={"cli": ('-f', '--input-file')}
    )

    max_records: int = Schema(
        123,
        title="Max Records",
        description="Max number of records to process",
        gt=0,
        extras={'cli': ('-m', '--max-records')}
    )

```


## Hooks into the CLI Execution

- exception handler
- epilogue handler

Both of these cases can be customized to by passing in a function to the running/execution method. 


The exception handler should handle any logging or writing to stderr as well as mapping the specific exception to non-zero integer exit code. 

For example: 

```python
import sys

from pydantic_cli import run_and_exit


def custom_exception_handler(ex) -> int:
    exception_map = dict(ValueError=3, IOError=7)
    sys.stderr.write(ex.getMessage)
    exit_code = exception_map.get(ex, 1)
    return exit_code


if __name__ == '__main__':
    run_and_exit(MinOptions, example_runner, exception_handler=custom_exception_handler)
```

Similarly, the post execution hook can be called. This function is `Callable[[int, float], None]` that is the exit code and program runtime in sec.


```python
import sys

from pydantic_cli import run_and_exit


def post_exe_hook_handler(exit_code: int, run_time_sec:float):
    m = "Success" if exit_code else "Failed"
    msg = f"Completed running ({m}) in {run_time_sec:.2f} sec"
    print(msg)


if __name__ == '__main__':
    run_and_exit(MinOptions, example_runner, epilogue_handler=post_exe_hook_handler)

```

## SubParsers

Defining a subparser to your commandline tool is enabled by creating a container `SubParser` dict and calling `run_sp_and_exit`


```python
import typing as T
from pydantic import BaseModel
from pydantic.schema import UrlStr


from pydantic_cli.examples import ConfigDefaults
from pydantic_cli import run_sp_and_exit, SubParser


class AlphaOptions(BaseModel):

    class Config(ConfigDefaults):
        CLI_EXTRA_OPTIONS = {'max_records': ('-m', '--max-records')}

    input_file: str
    max_records: int = 10


class BetaOptions(BaseModel):

    class Config(ConfigDefaults):
        CLI_EXTRA_OPTIONS = {'url': ('-u', '--url'),
                             'num_retries': ('-n', '--num-retries')}

    url: UrlStr
    num_retries: int = 3


def printer_runner(opts: T.Any):
    print(f"Mock example running with {opts}")
    return 0


def to_runner(sx):
    def example_runner(opts) -> int:
        print(f"Mock {sx} example running with {opts}")
        return 0
    return example_runner


def to_subparser_example():

    return {
        'alpha': SubParser(AlphaOptions, to_runner("Alpha"), "Alpha SP Description"),
        'beta': SubParser(BetaOptions, to_runner("Beta"), "Beta SP Description")}


if __name__ == "__main__":
    run_sp_and_exit(to_subparser_example(), description=__doc__, version='0.1.0')

```

# Limitations

- Currently **only support flat "simple" types** (e.g., floats, ints, strings, boolean). There's no current support for `List[T]` or nested dicts.
