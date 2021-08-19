# Pydantic Commandline Tool Interface

Turn Pydantic defined Data Models into CLI Tools and enable loading values from JSON files

**Requires Pydantic** `>=1.5.1`. 

[![Downloads](https://pepy.tech/badge/pydantic-cli)](https://pepy.tech/project/pydantic-cli)

[![Downloads](https://pepy.tech/badge/pydantic-cli/month)](https://pepy.tech/project/pydantic-cli)

## Installation

```bash
pip install pydantic-cli
```

## Features and Requirements

1. Thin Schema driven interfaces constructed from [Pydantic](https://github.com/samuelcolvin/pydantic) defined data models
1. Validation is performed in a single location as defined by Pydantic's validation model and defined types
1. CLI parsing is only structurally validating that the args or optional arguments are provided
1. Enable loading config defined in JSON to override or set specific values
1. Clear interface between the CLI and your application code
1. Leverage the static analyzing tool [**mypy**](http://mypy.readthedocs.io) to catch type errors in your commandline tool   
1. Easy to test (due to reasons defined above)


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

**WARNING**: Data models that have boolean values and generated CLI flags (e.g., `--enable-filter` or `--disable-filter`) require special attention. See the "Defining Boolean Flags" section for more details. 

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

## Catching Type Errors with mypy

If you've used `argparse`, you've probably been bitten by an `AttributeError` exception raised on the Namespace instance returned from parsing the raw args.

For example,

```python
import sys
from argparse import ArgumentParser


def to_parser() -> ArgumentParser:
    p = ArgumentParser(description="Example")
    f = p.add_argument

    f('hdf5_file', type=str, help="Path to HDF5 records")
    f("--num_records", required=True, type=int, help="Number of records to filter over")
    f('-f', '-filter-score', required=True, type=float, default=1.234, help="Min filter score")
    f('-g', '--enable-gamma-filter', action="store_true", help="Enable gamma filtering")
    return p


def my_library_code(path: str, num_records: float, min_filter_score, enable_gamma=True) -> int:
    print("Mock running of code")
    return 0


def main(argv) -> int:
    p = to_parser()
    pargs = p.parse_args(argv)
    return my_library_code(pargs.hdf5_file, pargs.num_record, pargs.min_filter_score, pargs.enable_gamma_filter)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

```

The first error found at runtime is show below. 

```bash
Traceback (most recent call last):
  File "junk.py", line 35, in <module>
    sys.exit(main(sys.argv[1:]))
  File "junk.py", line 31, in main
    return my_library_code(pargs.hdf5_file, pargs.num_record, pargs.min_filter_score, pargs.enable_gamma_filter)
AttributeError: 'Namespace' object has no attribute 'num_record'
```

The errors in `pargs.num_records` and `pargs.filter_score` are inconsistent with what is defined in `to_parser` method. Each error will have to be manually hunted down.

With `pydantic-cli`, it's possible to catch these errors by running `mypy`. This also enables you to refactor your code with more confidence.

For example,

```python
from pydantic import BaseModel

from pydantic_cli import run_and_exit


class Options(BaseModel):
    input_file: str
    max_records: int


def bad_func(n: int) -> int:
    return 2 * n


def example_runner(opts: Options) -> int:
    print(f"Mock example running with {opts}")
    return 0


if __name__ == "__main__":
    run_and_exit(Options, bad_func, version="0.1.0")
```

With `mypy`, it's possible to proactively catch this types of errors. 

```bash
 mypy pydantic_cli/examples/simple.py                                                                                                                                                                  ✘ 1 
pydantic_cli/examples/simple.py:36: error: Argument 2 to "run_and_exit" has incompatible type "Callable[[int], int]"; expected "Callable[[Options], int]"
Found 1 error in 1 file (checked 1 source file)

```

## Defining Boolean Flags

Boolean options in Pydantic data models require special attention. 

By default, when defining a model with a boolean flag, a "enable" or "disable" flag will be added depending on the default value.

For example.

```python
from pydantic import BaseModel

from pydantic_cli import run_and_exit


class Options(BaseModel):
    input_file: str
    run_training: bool = True
    dry_run: bool = False


def example_runner(opts: Options) -> int:
    print(f"Mock example running with {opts}")
    return 0


if __name__ == "__main__":
    run_and_exit(Options, example_runner, description=__doc__, version="0.1.0")
```

Since `run_training` has a default value of `True`, a commandline flag of `--disable-run_training` will be created. Enabling this from the commandline would set `run_training` in the Pydantic data model to `False`.

Similarly, `dry_run` has a default value of `False` and a commandline flag of `--enable-dry_run` will be created. Enabling this flag will set `dry_run` to True.

The default prefixes of the boolean flags are `(--enable-, --disable-)` and can configured in the configuration of the data model.

For example,

```python
from pydantic import BaseModel

from pydantic_cli import DefaultConfig


class Options(BaseModel):
    class Config(DefaultConfig):
        CLI_BOOL_PREFIX = ('--yes-', '--no-')

    input_file: str
    run_training: bool = True
    dry_run: bool = False
```

Similar to the non-boolean flags, the custom CLI options can be set. However, there's an important difference.

**Custom Boolean flags must be configured with BOTH True and False values** with a type of `Tuple[str, str]`. 

For example,


```python
from pydantic import BaseModel
from pydantic_cli import DefaultConfig

class Opts(BaseModel):
    class Config(DefaultConfig):
        CLI_EXTRA_OPTIONS = {'dry_run': ('--enable-dry-run', '--no-dry-run')}

    dry_run: bool = False
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
# Configuration Details and Advanced Features

Pydantic-cli attempts to stylistically follow Pydantic's approach using a class style configuration. See `DefaultConfig in ``pydantic_cli' for more details.

```python
import typing as T

class DefaultConfig:
    """
    Core Default Config "mixin" for CLI configuration.
    """

    # value used to generate the CLI format --{key}
    CLI_JSON_KEY: str = "json-config"
    # Enable JSON config loading
    CLI_JSON_ENABLE: bool = False

    # Set the default ENV var for defining the JSON config path
    CLI_JSON_CONFIG_ENV_VAR: str = "PCLI_JSON_CONFIG"
    # Set the default Path for JSON config file
    CLI_JSON_CONFIG_PATH: T.Optional[str] = None
    # If a default path is provided or provided from the commandline
    CLI_JSON_VALIDATE_PATH: bool = True

    # Can be used to override custom fields
    # e.g., {"max_records": ('-m', '--max-records')}
    # or {"max_records": ('-m', )}
    CLI_EXTRA_OPTIONS: T.Dict[str, CustomOptsType] = {}

    # Customize the default prefix that is generated
    # if a boolean flag is provided. Boolean custom CLI
    # MUST be provided as Tuple[str, str]
    CLI_BOOL_PREFIX: T.Tuple[str, str] = ("--enable-", "--disable-")

    # Add a flag that will emit the shell completion
    # this requires 'shtab'
    # https://github.com/iterative/shtab
    CLI_SHELL_COMPLETION_ENABLE: bool = False
    CLI_SHELL_COMPLETION_FLAG: str = "--emit-completion"
```

## AutoComplete leveraging shtab

There is support for `zsh` and `bash` autocomplete generation using [shtab](https://github.com/iterative/shtab)

The **optional** dependency can be installed as follows.
```bash
pip install "pydantic-cli[shtab]"
```

To enable the emitting of bash/zsh autocomplete files from shtab, set `CLI_SHELL_COMPLETION_ENABLE: bool = True` in your data model `Config`.

Then use your executable (or `.py` file) emit the autocomplete file to the necessary output directory. 

For example, using `zsh` and a script call `my-tool.py`, `my-tool.py --emit-completion zsh > ~/.zsh/completions/_my-tool.py`. By convention/default, the executable name must be prefixed with an underscore.  

When using autocomplete it should looks similar to this. 


```bash
> ./my-tool.py --emit-completion zsh > ~/.zsh/completions/_my-tool.py
Completed writing zsh shell output to stdout
> ./my-tool.py --max
 -- option --
--max_filter_score  --  (type:int default:1.0)
--max_length        --  (type:int default:12)
--max_records       --  (type:int default:123455)
--max_size          --  (type:int default:13)
```

See [shtab](https://github.com/iterative/shtab) for more details.


Note, that due to the (typically) global zsh completions directory, this can create some friction points with different virtual (or conda) ENVS with the same executable name.

# More Examples

[More examples are provided here](https://github.com/mpkocher/pydantic-cli/tree/master/pydantic_cli/examples)

# Limitations

- **Positional Arguments are not supported** (See more info the next subsection)
- Pydantic BaseSettings to set values from `dotenv` or ENV variables is **not supported**. Loading `dotenv` or similar in Pydantic overlapped and competed too much with the "preset" JSON loading model in `pydantic-cli`.
- [Pydantic has a perhaps counterintuitive model that sets default values based on the Type signature](https://pydantic-docs.helpmanual.io/usage/models/#required-optional-fields). For `Optional[T]` with NO default assign, a default of `None` is assigned. This can sometimes yield suprising commandline args generated from the Pydantic data model. 
- Currently **only support "simple" types** (e.g., floats, ints, strings, boolean) and limited support for fields defined as `List[T]` or `Set[T]`. There is **no support** for nested models.
- Leverages [argparse](https://docs.python.org/3/library/argparse.html#module-argparse) underneath the hood and argparse is a bit thorny of an API to build on top of.

## Why are Positional Arguments not supported?

The core features of pydantic-cli are:

- Define and validate models using Pydantic and use these schemas as an interface to the command line
- Leverage `mypy` (or similar static analyzer) to enable validating/checking typesafe-ness prior to runtime
- Load partial or complete models using JSON (these are essentially, partial or complete config or "preset" files)

Positional arguments create friction points when combined with loading model values from a JSON file. More specifically, (required) positional values of the model could be supplied in the JSON and are no longer required at the command line. 

For example:

```python
from pydantic import BaseModel
from pydantic_cli import DefaultConfig

class MinOptions(BaseModel):
    class Config(DefaultConfig):
        CLI_JSON_ENABLE = True
    
    input_file: str
    input_hdf: str
    max_records: int = 100
```

And the vanilla case running from the command line works as expected.

```bash
my-tool /path/to/file.txt /path/to/file.h5 --max_records 200
```

However, when using the JSON "preset" feature, there are potential problems where the positional arguments of the tool are shifting around depending on what fields have been defined in the JSON preset.

For example, running with this `preset.json`, the `input_file` positional argument is no longer required. 

```json
{"input_file": "/system/config.txt", "max_records": 12345}
```

Vanilla case works as expected.

```bash
my-tool  file.txt /path/to/file.h5 --json-config ./preset.json
```

However, this also works as well.

```bash
my-tool  /path/to/file.h5 --json-config ./preset.json
```

In my experience, **the changing of the semantic meaning of the command line tool's positional arguments depending on the contents of the `preset.json` created issues and bugs**.

The simplest fix is to remove the positional arguments in favor of `-i` or similar which removed the issue.

```python
from pydantic import BaseModel
from pydantic_cli import run_and_exit, to_runner, DefaultConfig

class MinOptions(BaseModel):
    class Config(DefaultConfig):
        CLI_JSON_ENABLE = True
        CLI_EXTRA_OPTIONS = {'input_file': ('-i', ), 'input_hdf': ('-d', '--hdf'), 'max_records': ('-m', '--max-records')}
    
    input_file: str
    input_hdf: str
    max_records: int = 100
```

Running with the `preset.json` defined above, works as expected.

```bash
my-tool --hdf /path/to/file.h5 --json-config ./preset.json
```

As well as overriding the `-i`. 

```bash
my-tool -i file.txt --hdf /path/to/file.h5 --json-config ./preset.json
```

Or 

```bash
my-tool --hdf /path/to/file.h5 -i file.txt --json-config ./preset.json
```

This consistency was the motivation for removing positional argument support in earlier versions of `pydantic-cli`. 

# Other Related Tools

Other tools that leverage type annotations to create CLI tools. 

- [cyto](https://github.com/sbtinstruments/cyto) Pydantic based model leveraging Pydantic's settings sources. Supports nested values. Optional TOML support. (Leverages: click, pydantic)
- [typer](https://github.com/tiangolo/typer) Typer is a library for building CLI applications that users will love using and developers will love creating. Based on Python 3.6+ type hints. (Leverages: click)
- [glacier](https://github.com/relastle/glacier) Building Python CLI using docstrings and typehints (Leverages: click)
- [Typed-Settings](https://gitlab.com/sscherfke/typed-settings) Manage typed settings with attrs classes – for server processes as well as click applications (Leverages: attrs, click)
- [cliche](https://github.com/kootenpv/cliche) Build a simple command-line interface from your functions. (Leverages: argparse and type annotations/hints)
- [SimpleParsing](https://github.com/lebrice/SimpleParsing) Simple, Elegant, Typed Argument Parsing with argparse. (Leverages: dataclasses, argparse)
- [recline](https://github.com/NetApp/recline) This library helps you quickly implement an interactive command-based application in Python. (Leverages: argparse + type annotations/hints)
- [clippy](https://github.com/gowithfloat/clippy) Clippy crawls the abstract syntax tree (AST) of a Python file and generates a simple command-line interface. 
- [clize](https://github.com/epsy/clize) Turn Python functions into command-line interfaces (Leverages: attrs)
- [plac](https://github.com/micheles/plac)  Parsing the Command Line the Easy Way.
- [typedparse](https://github.com/khud/typedparse) Parser for command-line options based on type hints (Leverages: argparse and type annotations/hints)
- [paiargparse](https://github.com/Planet-AI-GmbH/paiargparse) Extension to the python argparser allowing to automatically generate a hierarchical argument list based on dataclasses. (Leverages: argparse + dataclasses)

# Stats

- [Github Star Growth of pydantic-cli](https://star-history.t9t.io/#mpkocher/pydantic-cli)
