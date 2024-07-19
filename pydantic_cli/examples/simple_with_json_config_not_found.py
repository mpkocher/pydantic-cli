import sys
import logging

from pydantic import BaseModel

from pydantic_cli import run_and_exit, CliConfig

log = logging.getLogger(__name__)


class Options(BaseModel):
    """For cases where you want a global configuration file
    that is completely ignored if not found, you can set
    cli_json_config_path = False.
    """

    model_config = CliConfig(
        frozen=True,
        cli_json_config_path="/path/to/file/that/does/not/exist/simple_schema.json",
        cli_json_enable=True,
        cli_json_validate_path=False,
    )

    input_file: str
    max_records: int = 10


def example_runner(opts: Options) -> int:
    log.info(f"Mock example running with options {opts}")
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    run_and_exit(Options, example_runner, description="Description", version="0.1.0")
