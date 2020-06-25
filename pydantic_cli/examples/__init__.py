import sys
import logging
import typing as T
from enum import Enum

log = logging.getLogger(__name__)


class ExampleConfigDefaults:
    # validate_all = True
    # validate_assignment = False
    allow_mutation = False


class LogLevel(str, Enum):
    # wish this was defined in the stdlib's logging as an enum
    INFO = "INFO"
    DEBUG = "DEBUG"
    WARN = "WARN"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


def prologue_handler(opts) -> T.NoReturn:
    """Define a general Prologue hook to setup logging for the application"""
    format_str = (
        "[%(levelname)s] %(asctime)s [%(name)s %(funcName)s %(lineno)d] %(message)s"
    )
    logging.basicConfig(level="DEBUG", stream=sys.stdout, format=format_str)
    log.info(f"Running {__file__} with {opts}")


def epilogue_handler(exit_code: int, run_time_sec: float) -> T.NoReturn:
    log.info(
        f"Completed running {__file__} with exit code {exit_code} in {run_time_sec} sec."
    )
