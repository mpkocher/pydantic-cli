import logging
import shlex
from unittest import TestCase

from pydantic_cli import to_runner
from pydantic_cli.examples.subparser import CMDS

log = logging.getLogger(__name__)


class TestExamples(TestCase):
    def _to_exit(self, xs: None | int) -> int:
        return 0 if xs is None else xs

    def _run_with_args(self, args: str):
        f = to_runner(CMDS)
        log.info(f"Running {f} with args {args}")
        exit_code = self._to_exit(f(shlex.split(args)))
        self.assertEqual(exit_code, 0)

    def test_alpha(self):
        self._run_with_args("alpha -i /path/to/file.txt -m 1234")

    def test_beta(self):
        self._run_with_args("beta --url http://google.com -n 3")
