from unittest import TestCase

from pydantic_cli import to_runner
from pydantic_cli.examples.simple_with_custom_and_setup_log import (Options, example_runner,
                                                                    prologue_handler, epilogue_handler)


class TestExamples(TestCase):

    def _run_with_args(self, args, exit_code=0):
        f = to_runner(Options, example_runner, prologue_handler=prologue_handler,
                      epilogue_handler=epilogue_handler)
        exit_code = f(args)
        self.assertEqual(exit_code, exit_code)

    def test_simple_01(self):
        self._run_with_args(['/path/to/file.txt'])

    def test_simple_02(self):
        self._run_with_args(['/path/to/file.txt', '-m', '1234', '--log_level', "INFO"])

    def test_simple_03(self):
        self._run_with_args(['/path/to/file.txt', '-m', '1234', '--log_level', "BAD_LOG_LEVEL"], 1)

