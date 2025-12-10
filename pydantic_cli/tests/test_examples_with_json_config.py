from . import _TestHarness, HarnessConfig

import json
from tempfile import NamedTemporaryFile
from pydantic_cli.examples.simple_with_json_config import Opts


class TestExample(_TestHarness[Opts]):

    CONFIG = HarnessConfig(Opts)

    def _run_cmd_with_config(self, config, more_args):
        with NamedTemporaryFile(mode="w", delete=True) as f:
            json.dump(config, f)
            f.flush()
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
        self._run_cmd_with_config(opt.model_dump(), [])

    def test_simple_partial_json(self):
        config = dict(max_records=12, min_filter_score=1.024, alpha=1.234, beta=9.854)

        self._run_cmd_with_config(config, ["/path/to/file.hdf5"])
