from pydantic_cli.examples.simple_with_boolean import Options, example_runner

from . import _TestHarness, HarnessConfig


class TestExamples(_TestHarness[Options]):
    CONFIG = HarnessConfig(Options, example_runner)

    def test_simple_01(self):
        self.run_config(["--input_file", "/path/to/file.txt"])

    def test_simple_02(self):
        self.run_config(["--input_file", "/path/to/file.txt", "--disable-run_training"])

    def test_simple_03(self):
        self.run_config(
            [
                "--input_file",
                "/path/to/file.txt",
                "--disable-run_training",
                "--enable-dry_run",
            ]
        )
