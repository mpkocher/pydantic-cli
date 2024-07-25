from . import _TestHarness, HarnessConfig

from pydantic_cli.examples.simple_with_enum_by_name import Options


class TestExamples(_TestHarness[Options]):

    CONFIG = HarnessConfig(Options)

    def test_simple_01(self):
        args = ["--states", "RUNNING", "FAILED", "--mode", "alpha"]
        self.run_config(args)

    def test_case_insensitive(self):
        args = ["--states", "successful", "failed", "--mode", "ALPHA"]
        self.run_config(args)

    def test_bad_enum_by_value(self):
        args = [
            "--states",
            "RUNNING",
            "--mode",
            "1",
        ]
        self.run_config(args, exit_code=1)

    def test_bad_enum_value(self):
        args = [
            "--states",
            "RUNNING",
            "--mode",
            "DRAGON",
        ]
        self.run_config(args, exit_code=1)
