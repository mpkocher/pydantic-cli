from . import _TestHarness, HarnessConfig

from pydantic_cli.examples.simple import Options, example_runner


class TestExamples(_TestHarness[Options]):

    CONFIG = HarnessConfig(Options, example_runner)

    def test_simple_01(self):
        self.run_config(["--input_file", "/path/to/file.txt", "--max_record", "1234"])
