from pydantic_cli import to_runner
from pydantic_cli.examples.simple_with_boolean import Options, example_runner

from . import _TestUtil, TestConfig


class TestExamples(_TestUtil):
    CONFIG = TestConfig(model=Options, runner=example_runner)

    def test_simple_01(self):
        self.run_config(["--input_file", "/path/to/file.txt", '--run_training', 'True'])

