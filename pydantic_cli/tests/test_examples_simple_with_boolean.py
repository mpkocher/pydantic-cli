from pydantic_cli.examples.simple_with_boolean import Options, example_runner

from . import _TestHarness, TestConfig


class TestExamples(_TestHarness[Options]):
    CONFIG = TestConfig(Options, example_runner)

    def test_simple_01(self):
        self.run_config(["--input_file", "/path/to/file.txt", "--run_training", "True"])
