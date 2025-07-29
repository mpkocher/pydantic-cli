from pydantic_cli.examples.simple_schema import Options

from . import _TestHarness, HarnessConfig


class TestExamples(_TestHarness):
    CONFIG = HarnessConfig(Options)

    def test_01(self):
        args = "-f /path/to/file.txt -m 1234 -s 1.234 --max-filter-score 10.234 -n none"
        self.run_config(args.split())

    def test_02(self):
        args = "-f /path/to/file.txt -m 1234 -s 1.234 -S 10.234 --filter-name alphax"
        self.run_config(args.split())

    def test_03(self):
        self.run_config(["-f", "/path/to/file.txt", "-m", "1234", "-s", "1.234", "-n", "beta.v2"])
