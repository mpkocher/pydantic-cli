from . import _TestHarness, HarnessConfig

import json
from tempfile import NamedTemporaryFile
from pydantic_cli.examples.simple_with_json_config import Opts, runner


class TestExample(_TestHarness[Opts]):

    CONFIG = HarnessConfig(Opts, runner)

    def _util(self, d, more_args):
        with NamedTemporaryFile(mode="w", delete=False) as f:
            json.dump(d, f)
            f.flush()
            f.name
            args = ["--json-training", str(f.name)] + more_args
            self.run_config(args)

    def test_simple_json(self):
        opt = Opts(
            hdf_file="/path/to/file.hdf5",
            max_records=12,
            min_filter_score=1.024,
            alpha=1.234,
            beta=9.854,
        )
        self._util(opt.dict(), [])

    def test_simple_partial_json(self):
        d = dict(max_records=12, min_filter_score=1.024, alpha=1.234, beta=9.854)

        self._util(d, ["--hdf_file", "/path/to/file.hdf5"])
