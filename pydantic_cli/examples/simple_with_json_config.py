"""
Example demonstrating how to configure JSON configuration file loading
by customizing the Pydantic's BaseModel.Config.

Setting `CLI_JSON_ENABLE` to True will add a `--json-config /path/to/file.json` option
to the commandline parser and can override default values. If a value is provided
required in the Pydantic data model and is supplied in the JSON file, the value
will **now become optional** as a commandline argument.

If both the JSON config file is supplied and a commandline argument is supplied,
the explicit commandline argument will **override** the value supplied in the
JSON file. This enables JSON files to be used as "presets".

The `CLI_JSON_KEY` can customize the commandline option field. By default it
is set to 'json-config` (which generates a `--json-config` commandline argument).

Similarly, `CLI_JSON_ENABLE`
"""
import logging
from pydantic import BaseModel
from pydantic_cli import run_and_exit, DefaultConfig
from pydantic_cli.examples import epilogue_handler, prologue_handler

log = logging.getLogger(__name__)


class Opts(BaseModel):
    class Config(DefaultConfig):
        CLI_JSON_KEY = "json-training"
        CLI_JSON_ENABLE = True

    hdf_file: str
    max_records: int = 10
    min_filter_score: float
    alpha: float
    beta: float


def runner(opts: Opts) -> int:
    print(f"Running with opts:{opts}")
    return 0


if __name__ == "__main__":
    run_and_exit(
        Opts,
        runner,
        description="My Tool Description",
        version="0.1.0",
        prologue_handler=prologue_handler,
        epilogue_handler=epilogue_handler,
    )
