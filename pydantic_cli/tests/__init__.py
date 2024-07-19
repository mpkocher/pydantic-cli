import unittest
from typing import TypeVar, Generic, Type
from typing import Callable as F


from pydantic import BaseModel

from pydantic_cli import (
    to_runner,
    default_prologue_handler,
    default_epilogue_handler,
    PrologueHandlerType,
    EpilogueHandlerType,
)

M = TypeVar("M", bound=BaseModel)


# Making this name a bit odd (from TestConfig)
# to get around Pytest complaining that
# it can't collect the "Test"
class HarnessConfig(Generic[M]):
    def __init__(
        self,
        model_class: Type[M],
        runner_func: F[[M], int],
        prologue: PrologueHandlerType = default_prologue_handler,
        epilogue: EpilogueHandlerType = default_epilogue_handler,
    ):
        self.model = model_class
        self.runner = runner_func
        self.prologue = prologue
        self.epilogue = epilogue


class _TestHarness(Generic[M], unittest.TestCase):
    CONFIG: HarnessConfig[M]

    def run_config(self, args, exit_code=0):
        f = to_runner(
            self.CONFIG.model,
            self.CONFIG.runner,
            prologue_handler=self.CONFIG.prologue,
            epilogue_handler=self.CONFIG.epilogue,
        )
        _exit_code = f(args)
        self.assertEqual(_exit_code, exit_code)
