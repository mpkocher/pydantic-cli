from pydantic_cli.examples.simple_with_custom import Options

from . import _TestHarness, HarnessConfig


class TestExamples(_TestHarness[Options]):
    CONFIG = HarnessConfig(Options)

    def test_simple_01(self):
        self.run_config(["-i", "/path/to/file.txt", "-f", "1.0", "-m", "2"])

    def test_simple_02(self):
        self.run_config(["-i", "/path/to/file.txt", "-f", "1.0"])
