from . import _TestHarness, HarnessConfig

from pydantic_cli.examples.simple_with_list import Options, example_runner


class TestExamples(_TestHarness[Options]):

    CONFIG = HarnessConfig(Options, example_runner)

    def test_simple_01(self):
        args = ["--input_file", "/path/to/file.txt", "/and/another/file.txt",
                "--max_record", "1234",
                "--filters", "alpha", "beta"]
        self.run_config(args)
