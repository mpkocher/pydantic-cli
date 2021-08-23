import os
from pydantic import BaseModel
from typing import Callable as F
import typing as T


M = T.TypeVar("M", bound=BaseModel)
CustomOptsType = T.Union[T.Tuple[str], T.Tuple[str, str]]
EpilogueHandlerType = F[[int, float], None]
PrologueHandlerType = F[[T.Any], None]
ExceptionHandlerType = F[[BaseException], int]


# Trying to adhere to Pydantic's style of defining the
# config with a "mixin" or class "husk" that is used as
# configuration mechanism. The internally used model is CliConfig
class DefaultConfig:
    """
    Core Default Config "mixin" for CLI configuration.
    """

    # value used to generate the CLI format --{key}
    CLI_JSON_KEY: str = "json-config"
    # Enable JSON config loading
    CLI_JSON_ENABLE: bool = False

    # Set the default ENV var for defining the JSON config path
    CLI_JSON_CONFIG_ENV_VAR: str = "PCLI_JSON_CONFIG"
    # Set the default Path for JSON config file
    CLI_JSON_CONFIG_PATH: T.Optional[str] = None
    # If a default path is provided or provided from the commandline
    CLI_JSON_VALIDATE_PATH: bool = True

    # Can be used to override custom fields
    # e.g., {"max_records": ('-m', '--max-records')}
    # or {"max_records": ('-m', )}
    # ****** THIS SHOULD NO LONGER BE USED **** Use pydantic.Field.
    CLI_EXTRA_OPTIONS: T.Dict[str, CustomOptsType] = {}

    # Customize the default prefix that is generated
    # if a boolean flag is provided. Boolean custom CLI
    # MUST be provided as Tuple[str, str]
    CLI_BOOL_PREFIX: T.Tuple[str, str] = ("--enable-", "--disable-")

    # Add a flag that will emit the shell completion
    # this requires 'shtab'
    # https://github.com/iterative/shtab
    CLI_SHELL_COMPLETION_ENABLE: bool = False
    CLI_SHELL_COMPLETION_FLAG: str = "--emit-completion"


class CliConfig(BaseModel):
    """Internal Model for encapsulating the core configuration of the CLI model"""

    class Config:
        # allow_mutation: bool = False
        validate_all = True
        validate_assignment = True

    json_config_key: str = DefaultConfig.CLI_JSON_KEY
    json_config_enable: bool = DefaultConfig.CLI_JSON_ENABLE
    json_config_env_var: str = DefaultConfig.CLI_JSON_CONFIG_ENV_VAR
    json_config_path: T.Optional[str] = DefaultConfig.CLI_JSON_CONFIG_PATH
    json_config_path_validate: bool = DefaultConfig.CLI_JSON_VALIDATE_PATH
    bool_prefix: T.Tuple[str, str] = DefaultConfig.CLI_BOOL_PREFIX
    custom_opts: T.Dict[str, CustomOptsType] = DefaultConfig.CLI_EXTRA_OPTIONS
    shell_completion_enable: bool = DefaultConfig.CLI_SHELL_COMPLETION_ENABLE
    shell_completion_flag: str = DefaultConfig.CLI_SHELL_COMPLETION_FLAG

    def json_config_key_sanitized(self):
        """
        Arg parse will do some munging on this due to
        it's Namespace attribute style.
        """
        # I don't really understand why argparse
        # didn't just use a dict.
        return self.json_config_key.replace("-", "_")


# This should really use final for 3.8 T.Final[CliConfig]
DEFAULT_CLI_CONFIG = CliConfig()


def _get_cli_config_from_model(cls: T.Type[M]) -> CliConfig:
    enable_json_config: bool = getattr(
        cls.Config, "CLI_JSON_ENABLE", DEFAULT_CLI_CONFIG.json_config_enable
    )
    json_key_field_name: str = getattr(
        cls.Config, "CLI_JSON_KEY", DEFAULT_CLI_CONFIG.json_config_key
    )

    json_config_env_var: str = getattr(
        cls.Config, "CLI_JSON_CONFIG_ENV_VAR", DEFAULT_CLI_CONFIG.json_config_env_var
    )

    json_config_path: T.Optional[str] = getattr(
        cls.Config, "CLI_JSON_CONFIG_PATH", DEFAULT_CLI_CONFIG.json_config_path
    )

    json_config_validate_path: bool = getattr(
        cls.Config,
        "CLI_JSON_VALIDATE_PATH",
        DEFAULT_CLI_CONFIG.json_config_path_validate,
    )

    # there's an important prioritization to be clear about here.
    # The env var will override the default set in the Pydantic Model Config
    # and the value of othe commandline will override the ENV var
    path: T.Optional[str] = os.environ.get(json_config_env_var, json_config_path)

    custom_opts: T.Dict[str, CustomOptsType] = getattr(
        cls.Config, "CLI_EXTRA_OPTIONS", DEFAULT_CLI_CONFIG.custom_opts
    )

    custom_bool_prefix: CustomOptsType = getattr(
        cls.Config, "CLI_BOOL_PREFIX", DEFAULT_CLI_CONFIG.bool_prefix
    )

    shell_compeltion_enable: bool = getattr(
        cls.Config,
        "CLI_SHELL_COMPLETION_ENABLE",
        DEFAULT_CLI_CONFIG.shell_completion_enable,
    )

    shell_completion_flag: T.Optional[str] = getattr(
        cls.Config,
        "CLI_SHELL_COMPLETION_FLAG",
        DEFAULT_CLI_CONFIG.shell_completion_flag,
    )

    return CliConfig(
        json_config_enable=enable_json_config,
        json_config_key=json_key_field_name,
        json_config_env_var=json_config_env_var,
        json_config_path=path,
        json_config_path_validate=json_config_validate_path,
        bool_prefix=custom_bool_prefix,
        custom_opts=custom_opts,
        shell_completion_enable=shell_compeltion_enable,
        shell_completion_flag=shell_completion_flag,
    )
