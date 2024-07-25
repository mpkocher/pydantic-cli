from . import _TestHarness, HarnessConfig

from pydantic_cli.examples.simple_with_enum import Options


class TestExamples(_TestHarness[Options]):

    CONFIG = HarnessConfig(Options)

    def test_simple_01(self):
        args = ["--states", "RUNNING", "FAILED", "--max_records", "1234", "--mode", "1"]
        self.run_config(args)

    def test_bad_enum_value(self):
        args = [
            "--states",
            "RUNNING",
            "BAD_STATE",
            "--max_records",
            "1234",
            "--mode",
            "1",
        ]
        self.run_config(args, exit_code=1)
