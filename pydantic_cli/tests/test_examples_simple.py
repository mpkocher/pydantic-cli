from unittest import TestCase

from pydantic_cli import to_runner
from pydantic_cli.examples.simple import Options, example_runner


class TestExamples(TestCase):

    def _run_with_args(self, args):
        f = to_runner(Options, example_runner)
        exit_code = f(args)
        self.assertEqual(exit_code, 0)

    def test_simple_01(self):
        self._run_with_args(['/path/to/file.txt'])

    def test_simple_02(self):
        self._run_with_args(['/path/to/file.txt', '--max_records', '1234'])

