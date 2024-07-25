from . import _TestHarness, HarnessConfig

from pydantic_cli.examples.simple_with_json_config_not_found import (
    Options,
)


class TestExamples(_TestHarness[Options]):

    CONFIG = HarnessConfig(Options)

    def test_simple_01(self):
        self.run_config(["--input_file", "/path/to/file.txt", "--max_record", "1234"])

    def test_simple_02(self):
        self.run_config(
            [
                "--input_file",
                "/path/to/file.txt",
                "--max_record",
                "1234",
                "--json-config",
                "/bad/path/file.json",
            ]
        )
