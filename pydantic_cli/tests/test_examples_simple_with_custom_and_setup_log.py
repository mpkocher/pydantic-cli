from pydantic_cli.examples.simple_with_custom_and_setup_log import (
    Options,
    example_runner,
    epilogue_handler,
    prologue_handler,
)
from . import _TestHarness, TestConfig


class TestExamples(_TestHarness[Options]):
    CONFIG = TestConfig(
        Options, example_runner, epilogue=epilogue_handler, prologue=prologue_handler,
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
