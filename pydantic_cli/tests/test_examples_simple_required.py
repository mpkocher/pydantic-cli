from . import _TestHarness, HarnessConfig

from pydantic_cli.examples.simple import Options

class TestExamples(_TestHarness[Options]):

    CONFIG = HarnessConfig(Options)

    def test_simple_01(self):
        self.run_config(["/path/to/file.txt", "1234"])
