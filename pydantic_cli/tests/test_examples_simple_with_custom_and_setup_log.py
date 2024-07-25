from pydantic_cli.examples.simple_with_custom_and_setup_log import (
    Options,
    epilogue_handler,
    prologue_handler,
)
from . import _TestHarness, HarnessConfig


class TestExamples(_TestHarness[Options]):
    CONFIG = HarnessConfig(
        Options,
        epilogue=epilogue_handler,
        prologue=prologue_handler,
    )

    def test_simple_01(self):
        self.run_config(["-i", "/path/to/file.txt"])

    def test_simple_02(self):
        self.run_config(
            ["-i", "/path/to/file.txt", "-m", "1234", "--log_level", "INFO"]
        )

    def test_simple_03(self):
        self.run_config(
            ["-i", "/path/to/file.txt", "-m", "1234", "--log_level", "BAD_LOG_LEVEL"],
            exit_code=1,
        )
