from pydantic_cli.examples.simple_with_custom import Options, example_runner

from . import _TestUtil, TestConfig


class TestExamples(_TestUtil):
    CONFIG = TestConfig(model=Options, runner=example_runner)

    def test_simple_01(self):
        self.run_config(["-i", "/path/to/file.txt", "-f", "1.0", "-m", "2"])

    def test_simple_02(self):
        self.run_config(["-i", "/path/to/file.txt", "-f", "1.0"])
