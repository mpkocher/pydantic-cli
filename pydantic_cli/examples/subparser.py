"""
Example of Using a Subparser
"""
import typing as T
from pydantic import BaseModel, AnyUrl


from pydantic_cli.examples import ConfigDefaults
from pydantic_cli import run_sp_and_exit, SubParser


class AlphaOptions(BaseModel):

    class Config(ConfigDefaults):
        CLI_EXTRA_OPTIONS = {'max_records': ('-m', '--max-records')}

    input_file: str
    max_records: int = 10


class BetaOptions(BaseModel):

    class Config(ConfigDefaults):
        CLI_EXTRA_OPTIONS = {'url': ('-u', '--url'),
                             'num_retries': ('-n', '--num-retries')}

    url: AnyUrl
    num_retries: int = 3


def printer_runner(opts: T.Any):
    print(f"Mock example running with {opts}")
    return 0


def to_runner(sx):
    def example_runner(opts) -> int:
        print(f"Mock {sx} example running with {opts}")
        return 0
    return example_runner


def to_subparser_example():

    return {
        'alpha': SubParser(AlphaOptions, to_runner("Alpha"), "Alpha SP Description"),
        'beta': SubParser(BetaOptions, to_runner("Beta"), "Beta SP Description")}


if __name__ == "__main__":
    run_sp_and_exit(to_subparser_example(), description=__doc__, version='0.1.0')