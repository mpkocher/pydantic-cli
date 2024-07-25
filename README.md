# Pydantic Commandline Tool Interface

Turn Pydantic defined Data Models into CLI Tools and enable loading values from JSON files

**Requires Pydantic** `>=2.8.2`. 

[![Downloads](https://pepy.tech/badge/pydantic-cli)](https://pepy.tech/project/pydantic-cli)

[![Downloads](https://pepy.tech/badge/pydantic-cli/month)](https://pepy.tech/project/pydantic-cli)

## Installation

```bash
pip install pydantic-cli
```

## Features and Requirements

1. Thin Schema driven interfaces constructed from [Pydantic](https://github.com/samuelcolvin/pydantic) defined data models
1. Validation is performed in a single location as defined by Pydantic's validation model and defined types
1. The CLI parsing level is only structurally validating the args or optional arguments/flags are provided
1. Enable loading config defined in JSON to override or set specific values (e.g. `mytool -i in.csv --json-conf config.json`)
1. Clear interface between the CLI and your application code
1. Leverage the static analyzing tool [**mypy**](http://mypy.readthedocs.io) to catch type errors in your commandline tool   
1. Easy to test (due to reasons defined above)

### Motivating Use cases

- Quick scrapy commandline tools for local development (e.g., webscraper CLI tool, or CLI application that runs a training algo)
- Internal tools driven by a Pydantic data model/schema
- Configuration heavy tools that are driven by either partial (i.e, "presets") or complete configuration files defined using JSON

Note: Newer version of `Pydantic-settings` has support for commandline functionality. It allows mixing of "sources", such as ENV, YAML, JSON and might satisfy your requirements.  

https://docs.pydantic.dev/2.8/concepts/pydantic_settings/#settings-management

`Pydantic-cli` predates the CLI component of `pydantic-settings` and has a few different requirements and design approach. 

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
from pydantic_cli import run_and_exit, to_runner, Cmd


class MinOptions(Cmd):
    input_file: str
    max_records: int

    def run(self) -> None:
        print(f"Mock example running with {self}")


if __name__ == '__main__':
    # to_runner will return a function that takes the args list to run and 
    # will return an integer exit code
    sys.exit(to_runner(MinOptions, version='0.1.0')(sys.argv[1:]))

```

Or to implicitly use `sys.argv[1:]`, leverage `run_and_exit` (`to_runner` is also useful for testing).

```python
if __name__ == '__main__':
    run_and_exit(MinOptions, description="My Tool Description", version='0.1.0')

```

## Customizing Description and Commandline Flags

If the Pydantic data model fields are reasonable well named (e.g., 'min_score', or 'max_records'), this can yield a good enough description when `--help` is called. 

Customizing the commandline flags or the description can be done by leveraging  `description` keyword argument in `Field` from `pydantic`. See [`Field` model in Pydantic](https://pydantic-docs.helpmanual.io/usage/schema/) more details. 

Custom 'short' or 'long' forms of the commandline args can be provided by using a `Tuple[str]` or `Tuple2[str, str]`. For example, `cli=('-m', '--max-records')` or `cli=('--max-records',)`.

**Note**, Pydantic interprets `...` as a "required" value when used in `Field`.

https://docs.pydantic.dev/latest/concepts/models/#required-fields

```python
from pydantic import Field
from pydantic_cli import run_and_exit, Cmd


class MinOptions(Cmd):
    input_file: str = Field(..., description="Path to Input H5 file", cli=('-i', '--input-file'))
    max_records: int = Field(..., description="Max records to process", cli=('-m', '--max-records'))
    debug: bool = Field(False, description="Enable debugging mode", cli= ('-d', '--debug'))

    def run(self) -> None:
        print(f"Mock example running with options {self}")


if __name__ == '__main__':
    run_and_exit(MinOptions, description="My Tool Description", version='0.1.0')
```

Running

```bash
$> mytool -i input.hdf5 --max-records 100 --debug y
Mock example running with options MinOptions(input_file="input.hdf5", max_records=100, debug=True)
```


Leveraging `Field` is also useful for validating inputs using the standard Pydantic for validation.  

```python
from pydantic import Field
from pydantic_cli import Cmd


class MinOptions(Cmd):
    input_file: str = Field(..., description="Path to Input H5 file", cli=('-i', '--input-file'))
    max_records: int = Field(..., gt=0, lte=1000, description="Max records to process", cli=('-m', '--max-records'))

    def run(self) -> None:
        print(f"Mock example running with options {self}")
```

See [Pydantic docs](https://docs.pydantic.dev/latest/concepts/validators/) for more details.

## Loading Configuration using JSON

User created commandline tools using `pydantic-cli` can also load entire models or **partially** defined Pydantic data models from JSON files.


For example, given the following Pydantic data model with the `cli_json_enable = True` in `CliConfig`. 

The `cli_json_key` will define the commandline argument (e.g., `config` will translate to `--config`). The default value is `json-config` (`--json-config`).

```python
from pydantic_cli import CliConfig, run_and_exit, Cmd

class Opts(Cmd):
    model_config = CliConfig(
        frozen=True, cli_json_key="json-training", cli_json_enable=True
    )

    hdf_file: str
    max_records: int = 10
    min_filter_score: float
    alpha: float
    beta: float
    
    def run(self) -> None:
        print(f"Running with opts:{self}")

if __name__ == '__main__':
    run_and_exit(Opts, description="My Tool Description", version='0.1.0')

```

Can be run with a JSON file that defines all the (required) values. 

```json
{"hdf_file": "/path/to/file.hdf5", "max_records": 5, "min_filter_score": 1.5, "alpha": 1.0, "beta": 1.0}
```

The tool can be executed as shown below. Note, options required at the commandline as defined in the `Opts` model (e.g., 'hdf_file', 'min_filter_score', 'alpha' and 'beta') are **NO longer required** values supplied to the commandline tool.
```bash
my-tool --json-training /path/to/file.json
```

To override values in the JSON config file, or provide the missing required values, simply provide the values at the commandline.

These values **will override** values defined in the JSON config file. The provides a general mechanism of using configuration "preset" files. 

```bash
my-tool --json-training /path/to/file.json --alpha -1.8 --max_records 100 
```

Similarly, a partially described data model can be used combined with explict values provided at the commandline.

In this example, `hdf_file` and `min_filter_score` are still required values that need to be provided to the commandline tool.

```json
{"max_records":10, "alpha":1.234, "beta":9.876}
``` 

```bash
my-tool --json-training /path/to/file.json --hdf_file /path/to/file.hdf5 --min_filter_score -12.34
```

**Note:** The mixing and matching of a config/preset JSON file and commandline args is the fundamental design requirement of `pydantic-cli`. 

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
from pydantic_cli import run_and_exit, Cmd


class Options(Cmd):
    input_file: str
    max_records: int

    def run(self) -> None:
        print(f"Mock example running with {self.max_score}")


if __name__ == "__main__":
    run_and_exit(Options, version="0.1.0")
```

With `mypy`, it's possible to proactively catch these types of errors. 


## Using Boolean Flags

There's an ergonomic tradeoff to lean on Pydantic and avoid some friction points at CLI level. This yields an explicit model, but slight added verboseness.

Summary:

- `xs:bool` can be set from commandline as `--xs true` or `--xs false`. Or [using Pydantic's casting](https://docs.pydantic.dev/2.8/api/standard_library_types/#booleans), `--xs yes` or `--xs y`. 
- `xs:Optional[bool]` can be set from commandline as `--xs true`, `--xs false`, or `--xs none`

For the `None` case, you can configure your Pydantic model to handle the casting/coercing/validation. Similarly, the bool casting should be configured in Pydantic.

Consider a basic model:

```python
from typing import Optional
from pydantic import Field
from pydantic_cli import run_and_exit, Cmd

class Options(Cmd):
    input_file: str
    max_records: int = Field(100, cli=('-m', '--max-records'))
    dry_run: bool = Field(default=False, description="Enable dry run mode", cli=('-d', '--dry-run'))
    filtering: Optional[bool]
    
    def run(self) -> None:
        print(f"Mock example running with {self}")
    

if __name__ == "__main__":
    run_and_exit(Options, description=__doc__, version="0.1.0")
```

In this case, 

- `dry_run` is an optional value with a default and can be set as `--dry-run yes` or `--dry-run no`
- `filtering` is a required value and can be set `--filtering true`, `--filtering False`, and `--filtering None`   

See the Pydantic docs for more details on boolean casting.

https://docs.pydantic.dev/2.8/api/standard_library_types/#booleans


## Customization and Hooks


## Hooks into the CLI Execution

There are three core hooks into the customization of CLI execution. 

- exception handler (log or write to stderr and map specific exception classes to integer exit codes)
- prologue handler (pre-execution hook)
- epilogue handler (post-execution hook)

Both of these cases can be customized by passing in a function to the running/execution method. 


The exception handler should handle any logging or writing to stderr as well as mapping the specific exception to non-zero integer exit code. 

For example: 

```python
import sys

from pydantic import Field
from pydantic_cli import run_and_exit, Cmd


class MinOptions(Cmd):
    input_file: str = Field(..., cli=('-i',))
    max_records: int = Field(10, cli=('-m', '--max-records'))

    def run(self) -> None:
        # example/mock error raised. Will be mapped to exit code 3 
        raise ValueError(f"No records found in input file {self.input_file}")


def custom_exception_handler(ex: Exception) -> int:
    exception_map = dict(ValueError=3, IOError=7)
    sys.stderr.write(str(ex))
    exit_code = exception_map.get(ex.__class__, 1)
    return exit_code


if __name__ == '__main__':
    run_and_exit(MinOptions, exception_handler=custom_exception_handler)
```

A general pre-execution hook can be called using the `prologue_handler`. This function is `Callable[[T], None]`, where `T` is an instance of your Pydantic data model.

This setup hook will be called before the execution of your main function (e.g., `example_runner`).


```python
import sys
import logging

def custom_prologue_handler(opts) -> None:
    logging.basicConfig(level="DEBUG", stream=sys.stdout)

if __name__ == '__main__':
    run_and_exit(MinOptions, prolgue_handler=custom_prologue_handler)
```


Similarly, the post execution hook can be called. This function is `Callable[[int, float], None]` that is the `exit code` and `program runtime` in sec as input.


```python
from pydantic_cli import run_and_exit


def custom_epilogue_handler(exit_code: int, run_time_sec:float) -> None:
    m = "Success" if exit_code else "Failed"
    msg = f"Completed running ({m}) in {run_time_sec:.2f} sec"
    print(msg)


if __name__ == '__main__':
    run_and_exit(MinOptions, epilogue_handler=custom_epilogue_handler)

```

## SubParsers

Defining a subcommand to your commandline tool is enabled by creating a container of `dict[str, Cmd]` (with `str` is the subcommand name) into `run_and_exit` (or `to_runner`). 


```python
"""Example Subcommand Tool"""
from pydantic import AnyUrl, Field
from pydantic_cli import run_and_exit, Cmd


class AlphaOptions(Cmd):
    input_file: str = Field(..., cli=('-i',))
    max_records: int = Field(10, cli=('-m', '--max-records'))
    
    def run(self) -> None:
        print(f"Running alpha with {self}")


class BetaOptions(Cmd):
    """Beta command for testing. Description of tool"""
    url: AnyUrl = Field(..., cli=('-u', '--url'))
    num_retries: int = Field(3, cli=('-n', '--num-retries'))
    
    def run(self) -> None:
        print(f"Running beta with {self}")


if __name__ == "__main__":
    run_and_exit({"alpha": AlphaOptions, "beta": BetaOptions}, description=__doc__, version='0.1.0')

```
# Configuration Details and Advanced Features

Pydantic-cli attempts to stylistically follow Pydantic's approach using a class style configuration. See `DefaultConfig in ``pydantic_cli' for more details.

```python
import typing as T
from pydantic import ConfigDict


class CliConfig(ConfigDict, total=False):
    # value used to generate the CLI format --{key}
    cli_json_key: str
    # Enable JSON config loading
    cli_json_enable: bool

    # Set the default ENV var for defining the JSON config path
    cli_json_config_env_var: str
    # Set the default Path for JSON config file
    cli_json_config_path: T.Optional[str]
    # If a default path is provided or provided from the commandline
    cli_json_validate_path: bool

    # Add a flag that will emit the shell completion
    # this requires 'shtab'
    # https://github.com/iterative/shtab
    cli_shell_completion_enable: bool
    cli_shell_completion_flag: str
```

## AutoComplete leveraging shtab

There is support for `zsh` and `bash` autocomplete generation using [shtab](https://github.com/iterative/shtab)

The **optional** dependency can be installed as follows.
```bash
pip install "pydantic-cli[shtab]"
```

To enable the emitting of bash/zsh autocomplete files from shtab, set `CliConfig(cli_shell_completion_enable=True)` in your data model config.

Then use your executable (or `.py` file) emit the autocomplete file to the necessary output directory. 

For example, using `zsh` and a script call `my-tool.py`, `my-tool.py --emit-completion zsh > ~/.zsh/completions/_my-tool.py`. By convention/default, the executable name must be prefixed with an underscore.  

When using autocomplete it should look similar to this. 


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

# General Suggested Testing Model

At a high level, `pydantic_cli` is (hopefully) a thin bridge between your `Options` defined as a Pydantic model and your 
main `Cmd.run() -> None` method that has hooks into the startup, shutdown and error handling of the command line tool. 
It also supports loading config files defined as JSON. By design, `pydantic_cli` explicitly **does not expose, or leak the argparse instance** or implementation details. 
Argparse is a bit thorny and was written in a different era of Python. Exposing these implementation details would add too much surface area and would enable users' to start mucking with the argparse instance in all kinds of unexpected ways. 

Testing can be done by leveraging the `to_runner` interface.  


1. It's recommend trying to do the majority of testing via unit tests (independent of `pydantic_cli`) with your main function and different instances of your pydantic data model.
2. Once this test coverage is reasonable, it can be useful to add a few smoke tests at the integration level leveraging `to_runner` to make sure the tool is functional. Any bugs at this level are probably at the `pydantic_cli` level, not your library code.

Note, that `to_runner(Opts)` returns a `Callable[[List[str]], int]` that can be used with `sys.argv[1:]` to return an integer exit code of your program. The `to_runner` layer will also catch any exceptions. 

```python
import unittest

from pydantic_cli import to_runner, Cmd


class Options(Cmd):
    alpha: int
    
    def run(self) -> None:
        if self.alpha < 0:
            raise Exception(f"Got options {self}. Forced raise for testing.")



class TestExample(unittest.TestCase):

    def test_core(self):
        # Note, this has nothing to do with pydantic_cli
        # If possible, this is where the bulk of the testing should be
        # You code should raise exceptions here or return None on success
        self.assertTrue(Options(alpha=1).run() is None)

    def test_example(self):
        # This is intended to mimic end-to-end testing 
        # from argv[1:]. The exception handler will map exceptions to int exit codes.   
        f = to_runner(Options)
        self.assertEqual(1, f(["--alpha", "100"]))

    def test_expected_error(self):
        f = to_runner(Options)
        self.assertEqual(1, f(["--alpha", "-10"]))
```



For more scrappy, interactive local development, it can be useful to add `ipdb` or `pdb` and create a custom `exception_handler`.

```python
from pydantic_cli import default_exception_handler, run_and_exit, Cmd


class Options(Cmd):
    alpha: int
    
    def run(self) -> None:
        if self.alpha < 0:
            raise Exception(f"Got options {self}. Forced raise for testing.")

def exception_handler(ex: BaseException) -> int:
    exit_code = default_exception_handler(ex)
    import ipdb; ipdb.set_trace()
    return exit_code


if __name__ == "__main__":
    run_and_exit(Options, exception_handler=exception_handler)
```


The core design choice in `pydantic_cli` is leveraging composable functions `f(g(x))` style providing a straight-forward mechanism to plug into.

# More Examples

[More examples are provided here](https://github.com/mpkocher/pydantic-cli/tree/master/pydantic_cli/examples) and [Testing Examples can be seen here](https://github.com/mpkocher/pydantic-cli/tree/master/pydantic_cli/tests). 

The [TestHarness](https://github.com/mpkocher/pydantic-cli/blob/master/pydantic_cli/tests/__init__.py) might provide examples of how to test your CLI tool(s)

# Limitations

- **Positional Arguments are not supported** (See more info in the next subsection)
- Using Pydantic BaseSettings to set values from `dotenv` or ENV variables is **not supported**. Loading `dotenv` or similar in Pydantic overlapped and competed too much with the "preset" JSON loading model in `pydantic-cli`.
- Currently **only support "simple" types** (e.g., floats, ints, strings, boolean) and limited support for fields defined as `List[T]`, `Set[T]` and simple `Enum`s. There is **no support** for nested models. Pydantic-settings might be a better fit for these cases.
- Leverages [argparse](https://docs.python.org/3/library/argparse.html#module-argparse) underneath the hood (argparse is a bit thorny of an API to build on top of).

## Why are Positional Arguments not supported?

The core features of pydantic-cli are:

- Define and validate models using Pydantic and use these schemas as an interface to the command line
- Leverage `mypy` (or similar static analyzer) to enable validating/checking typesafe-ness prior to runtime
- Load partial or complete models using JSON (these are essentially, partial or complete config or "preset" files)

Positional arguments create friction points when combined with loading model values from a JSON file. More specifically, (required) positional values of the model could be supplied in the JSON and are no longer required at the command line. This can fundamentally change the commandline interface and create ambiguities/bugs.

For example:

```python
from pydantic_cli import CliConfig, Cmd


class MinOptions(Cmd):
    model_config = CliConfig(cli_json_enable=True)
    
    input_file: str
    input_hdf: str
    max_records: int = 100

    def run(self) -> None:
        print(f"Running with mock {self}")
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
from pydantic import Field
from pydantic_cli import CliConfig, Cmd

class MinOptions(Cmd):
    model_config = CliConfig(cli_json_enable=True)
    
    input_file: str = Field(..., cli=('-i', ))
    input_hdf: str = Field(..., cli=('-d', '--hdf'))
    max_records: int = Field(100, cli=('-m', '--max-records'))

    def run(self) -> None:
        print(f"Running {self}")
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

- [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/#command-line-support) Pydantic >= 2.8.2 supports CLI as a settings "source". 
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
- [piou](https://github.com/Andarius/piou) A CLI tool to build beautiful command-line interfaces with type validation.
- [pyrallis](https://github.com/eladrich/pyrallis) A framework for simple dataclass-based configurations.
- [ConfigArgParse](https://github.com/bw2/ConfigArgParse) A drop-in replacement for argparse that allows options to also be set via config files and/or environment variables.
- [spock](https://github.com/fidelity/spock) spock is a framework that helps manage complex parameter configurations during research and development of Python applications. (Leverages: argparse, attrs, and type annotations/hints)
- [oneFace](https://github.com/Nanguage/oneFace) Generating interfaces(CLI, Qt GUI, Dash web app) from a Python function.
- [configpile](https://github.com/denisrosset/configpile) Overlay for argparse that takes additional parameters from environment variables and configuration files

# Stats

- [Github Star Growth of pydantic-cli](https://star-history.t9t.io/#mpkocher/pydantic-cli)
