from . import _TestHarness, HarnessConfig

from pydantic_cli.examples.simple_with_enum_by_name import Options, example_runner


class TestExamples(_TestHarness[Options]):

    CONFIG = HarnessConfig(Options, example_runner)

    def test_simple_01(self):
        args = ["--favorite_animal", "CAT", "--animals", "CAT", "DOG"]
        self.run_config(args)

    def test_bad_enum_value(self):
        args = [
            "--favorite_animal",
            "DOG",
            "--animals",
            "CAT",
            "BAD_ANIMAL"
        ]
        self.run_config(args, exit_code=2)
