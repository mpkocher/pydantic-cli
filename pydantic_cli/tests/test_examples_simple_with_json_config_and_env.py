import json
import os
from tempfile import NamedTemporaryFile

from . import _TestHarness, HarnessConfig

from pydantic_cli.examples.simple_with_json_config_not_found import (
    Options,
)


class TestExamples(_TestHarness[Options]):

    CONFIG = HarnessConfig(Options)

    def test_simple_01(self):
        self.run_config(["--input_file", "/path/to/file.txt", "--max_record", "1234"])

    def test_simple_02(self):
        t = NamedTemporaryFile(mode="w", delete=True)
        d = dict(input_file="/path/to/input.txt", max_records=12345)

        with open(t.name, "w") as f:
            json.dump(d, f)

        env_var = "PCLI_JSON_CONFIG"
        os.environ.setdefault(env_var, t.name)
        self.run_config(["--input_file", "/path/to/file.txt", "--max_record", "1234"])
        os.environ.pop(env_var)
