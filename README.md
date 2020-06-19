# Pydantic Commandline Tool Interface

Turn Pydantic defined Data Models into CLI Tools!

**Requires Pydantic** `>=1.5.1`. 

## Features

1. Schema driven interfaces built on top of [Pydantic](https://github.com/samuelcolvin/pydantic) data models
2. Validation is performed in a single location as defined by Pydantic's validation model
3. CLI parsing is only structurally validating that the args or optional arguments are provided
4. Clear interface between the CLI and your application code
5. Easy to test (due to reasons defined above)


## Quick Start


To create a commandline tool that takes an input file and max number of records to process as positional arguments:

```bash
my-tool /path/to/file.txt 1234
```

This requires two components.

- Create Pydantic Data Model of type `T` 
- write a function that takes an instance of `T` and returns the exit code (e.g., 0 for success, non-zero for failure).
- pass the `T` into to the `to_runner` function, or the `run_and_exit`

Explicit example show below.  

```python
import sys

from pydantic import BaseModel
from pydantic_cli import run_and_exit, to_runner

class MinOptions(BaseModel):
    input_file: str
    max_records: int


def example_runner(opts: MinOptions) -> int:
    print(f"Mock example running with options {opts}")
    return 0

if __name__ == '__main__':
    # to_runner will return a function that takes the args list to run and 
    # will return an integer exit code
    sys.exit(to_runner(MinOptions, example_runner, version='0.1.0')(sys.argv[1:]))

```

Or to implicitly use `sys.argv[1:]`, call can leverage `run_and_exit` (`to_runner` is also useful for testing).

```python
if __name__ == '__main__':
    run_and_exit(MinOptions, example_runner, description="My Tool Description", version='0.1.0')

```

If the data model has default values, the commandline argument with be optional and the CLI arg will be prefixed with `--'.

For example:

```python
from pydantic import BaseModel
from pydantic_cli import run_and_exit

class MinOptions(BaseModel):
    input_file: str
    max_records: int = 10

    
def example_runner(opts: MinOptions) -> int:
    print(f"Mock example running with options {opts}")
    return 0
    
    
if __name__ == '__main__':
    run_and_exit(MinOptions, example_runner, description="My Tool Description", version='0.1.0')

```

Will create a tool with `my-tool /path/to/input.txt --max_records 1234`

```bash
my-tool /path/to/input.txt --max_records 1234
```

with `--max_records` being optional to the commandline interface.


**WARNING**: Boolean values must be communicated explicitly (e.g., `--run_training True`). This explicitness is chosen to avoid confusion with auto-generated option flags (`--is-run_training` or `--no-run_training`) that do not directly map to the core Pydantic data model.


The `--help` is quite minimal (due to the lack of metadata), however, verbosely named arguments can often be good enough to communicate the intent of the commandline interface.


For customization of the CLI args, such as max number of records is `-m 1234` in the above example, there are two approaches.

- The first is the "quick" method that is a minor change to the `Config` of the Pydantic Data model. 
- The second "Field" method is to define the metadata in the [`Field` model in Pydantic](https://pydantic-docs.helpmanual.io/usage/schema/) 


### Quick Model for Customization

We're going to change the usage from `my-tool /path/to/file.txt 1234` to `my-tool /path/to/file.txt -m 1234` .

This only requires adding  `CLI_EXTRA_OPTIONS` to the Pydantic `Config`.

```python
from pydantic import BaseModel

class MinOptions(BaseModel):

    class Config:
        CLI_EXTRA_OPTIONS = {'max_records': ('-m', )}

    input_file: str
    max_records: int = 10

```

You can also override the "long" argument. However, **note this is starting to add a new layer of indirection** on top of the Field. (e.g., 'max_records' to '--max-records') that may or may not be useful.


```python
from pydantic import BaseModel

class MinOptions(BaseModel):

    class Config:
        CLI_EXTRA_OPTIONS = {'max_records': ('-m', '--max-records')}

    input_file: str
    max_records: int = 10

```


### Schema Driven Approach using Pydantic Field


```python
from pydantic import BaseModel, Field


class Options(BaseModel):

    class Config:
        validate_all = True
        validate_assignment = True

    input_file: str = Field(
        ..., # this implicitly means required=True
        title="Input File",
        description="Path to the input file",
        required=True,
        extras={"cli": ('-f', '--input-file')}
    )

    max_records: int = Field(
        123,
        title="Max Records",
        description="Max number of records to process",
        gt=0,
        extras={'cli': ('-m', '--max-records')}
    )

```


## Hooks into the CLI Execution

- exception handler (log or write to stderr and map specific exception classes to integer exit codes)
- prologue handler (pre-execution hook)
- epilogue handler (post-execution hook)

Both of these cases can be customized to by passing in a function to the running/execution method. 


The exception handler should handle any logging or writing to stderr as well as mapping the specific exception to non-zero integer exit code. 

For example: 

```python
import sys

from pydantic_cli import run_and_exit


def custom_exception_handler(ex) -> int:
    exception_map = dict(ValueError=3, IOError=7)
    sys.stderr.write(str(ex))
    exit_code = exception_map.get(ex.__class__, 1)
    return exit_code


if __name__ == '__main__':
    run_and_exit(MinOptions, example_runner, exception_handler=custom_exception_handler)
```

A general pre-execution hook can be called using the `prologue_handler`. This function is `Callable[[T], None]`, where `T` is an instance of your Pydantic data model.

This setup hook will be called before the execution of your main function (e.g., `example_runner`).


```python
import sys
import logging

def custom_prologue_handler(opts) -> None:
    logging.basicConfig(level="DEBUG", stream=sys.stdout)

if __name__ == '__main__':
    run_and_exit(MinOptions, example_runner, prolgue_handler=custom_prologue_handler)
```


Similarly, the post execution hook can be called. This function is `Callable[[int, float], None]` that is the `exit code` and `program runtime` in sec as input.


```python
import sys

from pydantic_cli import run_and_exit


def custom_epilogue_handler(exit_code: int, run_time_sec:float):
    m = "Success" if exit_code else "Failed"
    msg = f"Completed running ({m}) in {run_time_sec:.2f} sec"
    print(msg)


if __name__ == '__main__':
    run_and_exit(MinOptions, example_runner, epilogue_handler=custom_epilogue_handler)

```

## SubParsers

Defining a subparser to your commandline tool is enabled by creating a container `SubParser` dict and calling `run_sp_and_exit`


```python
import typing as T
from pydantic import BaseModel, AnyUrl



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

    url: AnyUrl
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

# More Examples

[More examples are provided here](https://github.com/mpkocher/pydantic-cli/tree/master/pydantic_cli/examples)

# Limitations

- Currently **only support flat "simple" types** (e.g., floats, ints, strings, boolean). There's no current support for `List[T]` or nested dicts.
- Leverages [argparse](https://docs.python.org/3/library/argparse.html#module-argparse) underneath the hood and argparse is a bit thorny of an API to build on top of.


### To Improve

- Better type descriptions in help
- Better communication of required "options" in help
- Add load from JSON file