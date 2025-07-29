from . import _TestHarness, HarnessConfig

from pydantic_cli.examples.simple_with_list import Options


class TestExamples(_TestHarness[Options]):

    CONFIG = HarnessConfig(Options)

    def test_simple_01(self):
        args = [
            "--input_file",
            "/path/to/file.txt",
            "/and/another/file.txt",
            "--max_records",
            "1234",
            "--filters",
            "alpha",
            "beta",
        ]
        self.run_config(args)
