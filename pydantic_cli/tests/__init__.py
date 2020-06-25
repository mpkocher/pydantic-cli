import unittest
from typing import Callable, NamedTuple, TypeVar


from pydantic import BaseModel

from pydantic_cli import to_runner, default_prologue_handler, default_epilogue_handler

M = TypeVar('M', bound=BaseModel)


class TestConfig(NamedTuple):
    model: M
    runner: Callable
    prologue: Callable = default_prologue_handler
    epilogue: Callable = default_epilogue_handler


class _TestUtil(unittest.TestCase):

    CONFIG: TestConfig = None

    def run_config(self, args, exit_code=0):
        f = to_runner(self.CONFIG.model, self.CONFIG.runner,
                      prologue_handler=self.CONFIG.prologue, epilogue_handler=self.CONFIG.epilogue)
        _exit_code = f(args)
        self.assertEqual(_exit_code, exit_code)
