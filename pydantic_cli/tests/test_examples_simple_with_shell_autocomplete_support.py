from pydantic_cli.examples.simple_with_shell_autocomplete_support import (
    Options,
    example_runner,
)
from pydantic_cli.shell_completion import HAS_SHTAB

from . import _TestHarness, TestConfig


class TestExamples(_TestHarness[Options]):
    CONFIG = TestConfig(Options, example_runner)

    def test_simple_01(self):
        self.run_config(["-i", "/path/to/file.txt", "-f", "1.0", "-m", "2"])

    def test_simple_02(self):
        self.run_config(["-i", "/path/to/file.txt", "-f", "1.0"])

    def _test_auto_complete_shell(self, shell_id):
        if HAS_SHTAB:
            args = ["--emit-completion", shell_id]
        else:
            args = ["-i", "/path/to/file.txt", "-f", "1.0", "2"]
        self.run_config(args)

    def test_auto_complete_zsh(self):
        self._test_auto_complete_shell("zsh")

    def test_auto_complete_bash(self):
        self._test_auto_complete_shell("bash")
