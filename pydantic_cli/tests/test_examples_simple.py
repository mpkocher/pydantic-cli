from . import _TestUtil, TestConfig

from pydantic_cli.examples.simple import Options, example_runner


class TestExamples(_TestUtil):

    CONFIG = TestConfig(model=Options, runner=example_runner)

    def test_simple_01(self):
        self.run_config(["--input_file", "/path/to/file.txt", "--max_record", "1234"])
