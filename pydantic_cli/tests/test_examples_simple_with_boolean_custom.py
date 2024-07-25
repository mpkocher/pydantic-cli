from pydantic_cli.examples.simple_with_boolean_custom import Options

from . import _TestHarness, HarnessConfig


class TestExamples(_TestHarness[Options]):
    CONFIG = HarnessConfig(Options)

    def test_simple_01(self):
        self.run_config(
            [
                "--input_file",
                "/path/to/file.txt",
                "--input_file2",
                "/path/2.txt",
                "-f",
                "/path/to/file.h5",
                "--report_json",
                "output.json",
                "--fasta",
                "output.fasta",
                "--gamma",
                "true",
                "--alpha",
                "true",
                "--zeta_mode",
                "true",
                "--epsilon",
                "true",
                "--states",
                "RUNNING",
                "FAILED",
                "--filter_mode",
                "1",
            ]
        )
