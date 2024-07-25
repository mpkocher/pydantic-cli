import unittest
from typing import TypeVar, Generic, Type
from typing import Callable as F


from pydantic import BaseModel

from pydantic_cli import (
    Cmd,
    to_runner,
    default_prologue_handler,
    default_epilogue_handler,
    PrologueHandlerType,
    EpilogueHandlerType,
)

M = TypeVar("M", bound=Cmd)


# Making this name a bit odd (from TestConfig)
# to get around Pytest complaining that
# it can't collect the "Test"
class HarnessConfig(Generic[M]):
    def __init__(
        self,
        cmd: Type[M],
        prologue: PrologueHandlerType = default_prologue_handler,
        epilogue: EpilogueHandlerType = default_epilogue_handler,
    ):
        self.cmd = cmd
        self.prologue = prologue
        self.epilogue = epilogue


class _TestHarness(Generic[M], unittest.TestCase):
    CONFIG: HarnessConfig[M]

    def _to_exit(self, xs: None | int) -> int:
        # this is to handle the old model.
        # to_runner should now raise exceptions if there's
        # an issue
        return 0 if xs is None else xs

    def run_config(self, args: list[str], exit_code: int = 0):
        f = to_runner(
            self.CONFIG.cmd,
            prologue_handler=self.CONFIG.prologue,
            epilogue_handler=self.CONFIG.epilogue,
        )
        _exit_code = self._to_exit(f(args))
        self.assertEqual(_exit_code, exit_code)
