from pydantic_cli.examples.simple_with_boolean_and_config import Options, example_runner

from . import _TestHarness, TestConfig


class TestExamples(_TestHarness[Options]):
    CONFIG = TestConfig(Options, example_runner)

    def test_simple_01(self):
        self.run_config(["--input_file", "/path/to/file.txt"])

    def test_simple_02(self):
        self.run_config(["--input_file", "/path/to/file.txt", "--no-run_training"])

    def test_simple_03(self):
        self.run_config(
            ["--input_file", "/path/to/file.txt", "--no-run_training", "--yes-dry_run"]
        )
