from unittest import TestCase

from pydantic_cli import to_runner
from pydantic_cli.examples.simple_schema import Options, example_runner


class TestExamples(TestCase):

    def _run_with_args(self, args):
        f = to_runner(Options, example_runner)
        exit_code = f(args)
        self.assertEqual(exit_code, 0)

    def test_01(self):
        args = '-f /path/to/file.txt --max-records 1234 -s 1.234 --max-score 10.234'
        self._run_with_args(args.split())

    def test_02(self):
        self._run_with_args(['-f', '/path/to/file.txt', '--min-score', '12356'])

