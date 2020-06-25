from pydantic_cli import to_runner
from pydantic_cli.examples.simple_schema import Options, example_runner

from . import _TestUtil, TestConfig


class TestExamples(_TestUtil):
    CONFIG = TestConfig(model=Options, runner=example_runner)

    def test_01(self):
        args = '-f /path/to/file.txt --max_records 1234 -s 1.234 --max_filter_score 10.234'
        self.run_config(args.split())

    def test_02(self):
        args = '-f /path/to/file.txt -m 1234 -s 1.234 -S 10.234'
        self.run_config(args.split())

    def test_03(self):
        self.run_config(['-f', '/path/to/file.txt', '-s', '1.234'])

