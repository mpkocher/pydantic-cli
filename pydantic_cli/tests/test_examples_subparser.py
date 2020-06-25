import logging
from unittest import TestCase

from pydantic_cli import to_runner_sp
from pydantic_cli.examples.subparser import to_subparser_example

log = logging.getLogger(__name__)


class TestExamples(TestCase):
    def _run_with_args(self, args):
        f = to_runner_sp(to_subparser_example())
        log.info(f"Running {f} with args {args}")
        exit_code = f(args)
        self.assertEqual(exit_code, 0)

    def test_alpha(self):
        self._run_with_args(["alpha", "-i", "/path/to/file.txt", "-m", "1234"])

    def test_beta(self):
        self._run_with_args(["beta", "--url", "http://google.com", "-n", "3"])
