from pydantic_cli.examples.simple_with_boolean_custom import Options

from . import _TestHarness, HarnessConfig


class TestExamples(_TestHarness[Options]):
    CONFIG = HarnessConfig(Options)

    def test_simple_01(self):
        self.run_config(
            [
                "/path/to/file.txt",
                "/path/2.txt",
                "-f",
                "/path/to/file.h5",
                "output.json",
                "--fasta",
                "output.fasta",
                "true",
                "true",
                "true",
                "--epsilon",
                "true",
                "RUNNING",
                "FAILED",
                "1",
            ]
        )
