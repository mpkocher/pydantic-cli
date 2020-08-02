import os
import json
import warnings

import typing as T


def _load_json_file(json_path: str) -> T.Dict[str, T.Any]:
    with open(json_path, "r") as f:
        d: T.Dict[str, T.Any] = json.load(f)
    return d


def _resolve_path_or_none(path: str) -> T.Optional[str]:
    p = os.path.abspath(path)
    if os.path.exists(p):
        return p
    return None


def _resolve_file_or_none_and_warn(path: str) -> T.Optional[str]:
    p = _resolve_path_or_none(path)
    if p is None:
        warnings.warn(f"Unable to find {path}")
    return p


def _resolve_file(path: str) -> str:
    p = _resolve_path_or_none(path)
    if p is not None:
        return p
    raise IOError(f"Unable to find path ({path})")
