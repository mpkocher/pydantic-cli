from pydantic_cli.examples.simple_with_boolean import Options

from . import _TestHarness, HarnessConfig


class TestExamples(_TestHarness[Options]):
    CONFIG = HarnessConfig(Options)

    def test_simple_01(self):
        self.run_config(["/path/to/file.txt"])

    def test_simple_02(self):
        self.run_config(["/path/to/file.txt", "--run_training", "y"])

    def test_simple_03(self):
        self.run_config(
            [
                "/path/to/file.txt",
                "--run_training",
                "true",
                "--dry_run",
                "true",
            ]
        )
