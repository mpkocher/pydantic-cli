from . import _TestHarness, HarnessConfig, WithTempJsonFile

from pydantic_cli.examples.simple_with_json_config_and_namespace import Opts, runner

_NAMESPACE = "alpha"


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
        d = {_NAMESPACE: opt.dict()}
        with WithTempJsonFile(d) as f:
            args = ["--json-training", f.file_name, "--js-namespace", _NAMESPACE]
            self.run_config(args)

    def test_simple_partial_json(self):
        dx = dict(max_records=12, min_filter_score=1.024, alpha=1.234, beta=9.854)
        d = {_NAMESPACE: dx}
        with WithTempJsonFile(d) as f:
            args = [
                "--hdf_file",
                "/path/to/new/file.hdf5",
                "--js-namespace",
                _NAMESPACE,
                "--json-training",
                f.file_name,
            ]
            self.run_config(args)
