import os
from pydantic import ConfigDict, BaseModel
from typing import Callable as F
import typing as T


M = T.TypeVar("M", bound=BaseModel)
Tuple1Type = T.Tuple[str]
Tuple2Type = T.Tuple[str, str]
Tuple1or2Type = T.Union[Tuple1Type, Tuple2Type]
EpilogueHandlerType = F[[int, float], None]
PrologueHandlerType = F[[T.Any], None]
ExceptionHandlerType = F[[BaseException], int]


class CliConfig(ConfigDict, total=False):
    """
    See `_get_cli_config_from_model` for defaults.

    This is a container to work with pydantic's style of
    defining the config. We'll validate this internally
    and convert to a BaseModel
    """

    # value used to generate the CLI format --{key}
    cli_json_key: str
    # Enable JSON config loading
    cli_json_enable: bool

    # Set the default ENV var for defining the JSON config path
    cli_json_config_env_var: str
    # Set the default Path for JSON config file
    cli_json_config_path: T.Optional[str]
    # If a default path is provided or provided from the commandline
    cli_json_validate_path: bool

    # Add a flag that will emit the shell completion
    # this requires 'shtab'
    # https://github.com/iterative/shtab
    cli_shell_completion_enable: bool
    cli_shell_completion_flag: str


def _get_cli_config_from_model(cls: T.Type[M]) -> CliConfig:

    cli_json_key = T.cast(str, cls.model_config.get("cli_json_key", "json-config"))
    cli_json_enable: bool = T.cast(bool, cls.model_config.get("cli_json_enable", False))
    cli_json_config_env_var: str = T.cast(
        str, cls.model_config.get("cli_json_config_env_var", "PCLI_JSON_CONFIG")
    )
    cli_json_config_path_from_model: T.Optional[str] = T.cast(
        T.Optional[str], cls.model_config.get("cli_json_config_path")
    )
    cli_json_validate_path: bool = T.cast(
        bool, cls.model_config.get("cli_json_validate_path", True)
    )

    # there's an important prioritization to be clear about here.
    # The env var will override the default set in the Pydantic Model Config
    # and the value of the commandline will override the ENV var
    cli_json_config_path: T.Optional[str] = os.environ.get(
        cli_json_config_env_var, cli_json_config_path_from_model
    )

    cli_shell_completion_enable: bool = T.cast(
        bool, cls.model_config.get("cli_shell_completion_enable", False)
    )

    cli_shell_completion_flag = T.cast(
        str, cls.model_config.get("cli_shell_completion_flag", "--emit-completion")
    )
    return CliConfig(
        cli_json_key=cli_json_key,
        cli_json_enable=cli_json_enable,
        cli_json_config_env_var=cli_json_config_env_var,
        cli_json_config_path=cli_json_config_path,
        cli_json_validate_path=cli_json_validate_path,
        cli_shell_completion_enable=cli_shell_completion_enable,
        cli_shell_completion_flag=cli_shell_completion_flag,
    )
