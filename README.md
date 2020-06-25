# Pydantic Commandline Tool Interface

Turn Pydantic defined Data Models into CLI Tools and enable loading values from JSON files

**Requires Pydantic** `>=1.5.1`. 

## Features and Requirements

1. Thin Schema driven interfaces constructed from [Pydantic](https://github.com/samuelcolvin/pydantic) defined data models
2. Validation is performed in a single location as defined by Pydantic's validation model and defined types
3. CLI parsing is only structurally validating that the args or optional arguments are provided
4. Enable loading config defined in JSON to override or set specific values
5. Clear interface between the CLI and your application code  
6. Easy to test (due to reasons defined above)


## Quick Start


To create a commandline tool that takes an input file and max number of records to process as arguments:

```bash
my-tool --input_file /path/to/file.txt --max_records 1234
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

**WARNING**: Boolean values must be communicated explicitly (e.g., `--run_training True`). This explicitness is chosen to avoid confusion with auto-generated option flags (`--is-run_training` or `--no-run_training`) that do not directly map to the core Pydantic data model.


## Loading Configuration using JSON

Tools can also load entire models or partially defined Pydantic data models from JSON files.


For example, given the following Pydantic data model:

```python
from pydantic import BaseModel
from pydantic_cli import run_and_exit, DefaultConfig

class Opts(BaseModel):
    class Config(DefaultConfig):
        CLI_JSON_ENABLE = True
    
    hdf_file: str
    max_records: int = 10
    min_filter_score: float
    alpha: float
    beta: float

def runner(opts: Opts):
    print(f"Running with opts:{opts}")
    return 0

if __name__ == '__main__':
    run_and_exit(Opts, runner, description="My Tool Description", version='0.1.0')

```

Can be run with a JSON file that defines all the (required) values. 

```json
{"hdf_file": "/path/to/file.hdf5", "max_records": 5, "min_filter_score": 1.5, "alpha": 1.0, "beta": 1.0}
```

The tool can be executed as shown below. Note, options required at the commandline as defined in the `Opts` model (e.g., 'hdf_file', 'min_filter_score', 'alpha' and 'beta') are NO longer required values supplied to the commandline tool.
```bash
my-tool --json-config /path/to/file.json
```

To override values in the JSON config file, or provide the missing required values, simply provide the values at the commandline.

These values **will override** values defined in the JSON config file. The provides a general mechanism of using configuration "preset" files. 

```bash
my-tool --json-config /path/to/file.json --alpha -1.8 --max_records 100 
```

Similarly, a partially described data model can be used combined with explict values provided at the commandline.

In this example, `hdf_file` and `min_filter_score` are still required values that need to be provided to the commandline tool.

```json
{"max_records":10, "alpha":1.234, "beta":9.876}
``` 

```bash
my-tool --json-config /path/to/file.json --hdf_file /path/to/file.hdf5 --min_filter_score -12.34
```


## Customization and Hooks

If the `description` is not defined and the Pydantic data model fields are tersely named (e.g., 'total', or 'n'), this can yield a call to `--help` that is quite minimal (due to the lack of metadata). However, verbosely named arguments can often be good enough to communicate the intent of the commandline interface.


For customization of the CLI args, such as max number of records is `-m 1234` in the above example, there are two approaches.

- The first is the **quick** method that is a minor change to the core `Config` of the Pydantic Data model. 
- The second method is use Pydantic's "Field" metadata model is to define richer set of metadata. See [`Field` model in Pydantic](https://pydantic-docs.helpmanual.io/usage/schema/) more details. 


### Customization using Quick Model

We're going to change the usage from `my-tool --input_file /path/to/file.txt --max_records 1234` to `my-tool -i /path/to/file.txt -m 1234` using the "quick" method by customizing the Pydantic data model "Config".

This only requires adding  `CLI_EXTRA_OPTIONS` to the Pydantic `Config`.

```python
from pydantic import BaseModel

class MinOptions(BaseModel):

    class Config:
        CLI_EXTRA_OPTIONS = {'input_file': ('-i,), 'max_records': ('-m', ) }

    input_file: str
    max_records: int = 10

```

You can also override the "long" argument. However, **note this is starting to add a new layer of indirection** on top of the fields defined in the Pydantic model. For example, 'max_records' maps to '--max-records' at the commandline interface and perhaps might create annoying inconsistencies.


```python
from pydantic import BaseModel

class MinOptions(BaseModel):

    class Config:
        CLI_EXTRA_OPTIONS = {'input_file': ('-i, '), 'max_records': ('-m', '--max-records')}

    input_file: str
    max_records: int = 10

```


### Customization using Quick Model using Schema Driven Approach using Pydantic Field


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

This will metadata (e.g., title, description) will be communicated in the `--help` of the commandline tool.


## Hooks into the CLI Execution

There are three core hooks into the customization of CLI execution. 

- exception handler (log or write to stderr and map specific exception classes to integer exit codes)
- prologue handler (pre-execution hook)
- epilogue handler (post-execution hook)

Both of these cases can be customized to by passing in a function to the running/execution method. 


The exception handler should handle any logging or writing to stderr as well as mapping the specific exception to non-zero integer exit code. 

For example: 

```python
import sys

from pydantic import BaseModel
from pydantic_cli import run_and_exit


class MinOptions(BaseModel):

    class Config:
        CLI_EXTRA_OPTIONS = {'input_file': ('-i, '), 'max_records': ('-m', '--max-records')}

    input_file: str
    max_records: int = 10


def example_runner(opts: MinOptions) -> int:
    return 0


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



from pydantic_cli.examples import ExampleConfigDefaults
from pydantic_cli import run_sp_and_exit, SubParser


class AlphaOptions(BaseModel):

    class Config(ExampleConfigDefaults):
        CLI_EXTRA_OPTIONS = {'max_records': ('-m', '--max-records')}

    input_file: str
    max_records: int = 10


class BetaOptions(BaseModel):

    class Config(ExampleConfigDefaults):
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

- Better type descriptions in `--help`
- Better support for boolean values to avoid having `--run_training True` and have more natural CLI arg style, such as `--run_training` and `--no_run_training`.
- Better error messages