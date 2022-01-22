from . import _TestHarness, HarnessConfig, WithTempJsonFile

from pydantic_cli.examples.simple_with_json_config import Opts, runner


class TestExample(_TestHarness[Opts]):

    CONFIG = HarnessConfig(Opts, runner)

    def test_simple_json(self):
        opt = Opts(
            hdf_file="/path/to/file.hdf5",
            max_records=12,
            min_filter_score=1.024,
            alpha=1.234,
            beta=9.854,
        )
        with WithTempJsonFile(opt.dict()) as f:
            args = ["--json-training", f.file_name]
            self.run_config(args)

    def test_simple_partial_json(self):
        d = dict(max_records=12, min_filter_score=1.024, alpha=1.234, beta=9.854)

        with WithTempJsonFile(d) as f:
            args = ["--json-training", f.file_name, "--hdf_file", "/path/to/file.hdf5"]
            self.run_config(args)
