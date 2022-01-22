from . import _TestHarness, HarnessConfig, WithEnv, WithTempJsonFile

from pydantic_cli.examples.simple_with_json_config_not_found import (
    Options,
    example_runner,
)


class TestExamples(_TestHarness[Options]):

    CONFIG = HarnessConfig(Options, example_runner)

    def test_simple_01(self):
        self.run_config(["--input_file", "/path/to/file.txt",
                         "--max_record", "1234"])

    def _test_simple_02(self):
        d = dict(input_file="/path/to/input.txt", max_records=12345)
        env_var = "PCLI_JSON_CONFIG"
        with WithTempJsonFile(d) as f:
            with WithEnv(env_var, f.file_name):
                args = ["--input_file", "/path/to/file.txt", "--max_record", "1234"]
                self.run_config(args)
