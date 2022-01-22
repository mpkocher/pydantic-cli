import json
from dataclasses import dataclass
import os
import unittest
import logging
from tempfile import NamedTemporaryFile
from typing import TypeVar, Generic, Type, Dict
from typing import Callable as F


from pydantic import BaseModel

from pydantic_cli import (
    to_runner,
    default_prologue_handler,
    default_epilogue_handler,
    PrologueHandlerType,
    EpilogueHandlerType,
)

log = logging.getLogger(__name__)

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
        # log.debug(f"****ARGS={args}")
        _exit_code = f(args)
        self.assertEqual(_exit_code, exit_code)


@dataclass
class WithEnv:
    """Set and unset an ENV var"""
    env_name: str
    value: str

    def __enter__(self):
        os.environ.setdefault(self.env_name, self.value)

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.environ.pop(self.env_name)


class WithTempJsonFile:
    """Write a dict and create a temp file that will be deleted"""
    def __init__(self, values: Dict):
        self._values = values
        self._file = NamedTemporaryFile(mode="w", delete=True, suffix=".json")
        self.file_name = self._file.name

    def __enter__(self):
        with open(self.file_name, 'w') as f:
            json.dump(self._values, f)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._file.close()
