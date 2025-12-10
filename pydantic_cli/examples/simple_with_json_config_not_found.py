import sys
import logging

from pydantic import Field

from pydantic_cli import run_and_exit, CliConfig, Cmd

log = logging.getLogger(__name__)


class Options(Cmd):
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

    input_file: str = Field(cli=("--input_file",))
    max_records: int = 10

    def run(self) -> None:
        log.info(f"Mock example running with options {self}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    run_and_exit(Options, description="Description", version="0.1.0")
