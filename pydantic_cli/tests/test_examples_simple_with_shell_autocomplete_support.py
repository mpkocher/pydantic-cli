import unittest

from pydantic_cli.examples.simple_with_shell_autocomplete_support import (
    Options,
)
from pydantic_cli.shell_completion import HAS_AUTOCOMPLETE_SUPPORT

from . import _TestHarness, HarnessConfig


class TestExamples(_TestHarness[Options]):
    CONFIG = HarnessConfig(Options)

    def test_simple_01(self):
        self.run_config(["-i", "/path/to/file.txt", "-f", "1.0", "-m", "2"])

    def test_simple_02(self):
        self.run_config(["-i", "/path/to/file.txt", "-f", "1.0"])

    def _test_auto_complete_shell(self, shell_id):
        if HAS_AUTOCOMPLETE_SUPPORT:
            args = ["--emit-completion", shell_id]
            self.run_config(args)

    @unittest.skipIf(not HAS_AUTOCOMPLETE_SUPPORT, "shtab not installed")
    def test_auto_complete_zsh(self):
        self._test_auto_complete_shell("zsh")

    @unittest.skipIf(not HAS_AUTOCOMPLETE_SUPPORT, "shtab not installed")
    def test_auto_complete_bash(self):
        self._test_auto_complete_shell("bash")
