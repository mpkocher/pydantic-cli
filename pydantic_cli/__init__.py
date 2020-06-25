import datetime
import json
import sys
import traceback
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, SUPPRESS, Action
import logging
import typing as T
from typing import Callable as F


from pydantic import BaseModel

M = T.TypeVar("M", bound=BaseModel)

log = logging.getLogger(__name__)

NOT_PROVIDED = ...

VERSION = (2, 0, 0)

__version__ = ".".join([str(i) for i in VERSION])

__all__ = [
    "to_runner",
    "run_and_exit",
    "to_runner_sp",
    "run_sp_and_exit",
    "default_exception_handler",
    "default_prologue_handler",
    "default_epilogue_handler",
    "DefaultConfig",
]


class DefaultConfig:
    # value used to generate the CLI format --{key}
    CLI_JSON_KEY: str = "json-config"
    # Enable JSON config loading
    CLI_JSON_ENABLE: bool = False


class TerminalEagerCommand(Exception):
    """
    An "Eager" Action (e.g., --version, --help) has completed successfully

    This will be used as a Control structure to deal with the .exit()
    calls that are used on some Actions (e.g., Help, Version)
    """


class EagerHelpAction(Action):
    def __init__(self, option_strings, dest=SUPPRESS, default=SUPPRESS, help=None):
        super(EagerHelpAction, self).__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help,
        )

    def __call__(self, parser, namespace, values, option_string=None):
        parser.print_help()
        raise TerminalEagerCommand("Help completed running")


class EagerVersionAction(Action):
    def __init__(
        self,
        option_strings,
        version=__version__,
        dest=SUPPRESS,  # wtf does this do?
        default=SUPPRESS,
        help="show program's version number and exit",
    ):
        super(EagerVersionAction, self).__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help,
        )
        self.version = version

    def __call__(self, parser, namespace, values, option_string=None):
        version = self.version
        if version is None:
            version = parser.version
        formatter = parser._get_formatter()
        formatter.add_text(version)
        parser._print_message(formatter.format_help(), sys.stdout)
        raise TerminalEagerCommand("Version completed running")


class CustomArgumentParser(ArgumentParser):
    def exit(self, status: int = 0, message: T.Optional[T.Text] = None) -> T.NoReturn:
        # THIS IS NO longer used because of the custom Version and Help
        # This is a bit of an issue to return the exit code properly
        # log.debug(f"{self} Class:{self.__class__.__name__} called exit()")
        if status != 0:
            raise RuntimeError(f"Status ({status}) Failed to run command {message}")


class SubParser(T.NamedTuple):
    model_class: M
    runner_func: T.Callable
    description: T.Optional[T.Text]


def _parser_add_help(p: CustomArgumentParser):
    p.add_argument(
        "--help", help="Print Help and Exit", action=EagerHelpAction, default=SUPPRESS
    )
    return p


def _parser_add_version(parser: ArgumentParser, version: T.Text) -> ArgumentParser:
    parser.add_argument("--version", action=EagerVersionAction, version=version)
    return parser


def __to_field_description(
    default_value=NOT_PROVIDED, field_type=NOT_PROVIDED, description=None
):
    desc = "" if description is None else description
    t = "" if field_type is NOT_PROVIDED else f"type:{field_type}"
    v = "" if default_value is NOT_PROVIDED else f"default:{default_value}"
    if not (t + v):
        xs = "".join([t, v])
    else:
        xs = " ".join([t, v])
    return f"{desc} ({xs})"


def __process_tuple(tuple_one_or_two, long_arg) -> T.Tuple[str, str]:
    """
    If the custom args are provided as only short, then
    add the long version.
    """
    lx = list(tuple_one_or_two)

    def is_short(xs):
        # xs = '-s'
        return len(xs) == 2

    if len(lx) == 1:
        first = lx[0]
        if is_short(first):
            return first, long_arg
        else:
            return tuple_one_or_two
    else:
        return tuple_one_or_two


def _add_pydantic_field_to_parser(
    parser: CustomArgumentParser,
    field_id: str,
    field,
    override_value=...,
    override_cli: T.Optional[T.Text] = None,
    prefix="--",
) -> ArgumentParser:
    # field is Field from Pydantic
    description = field.field_info.description
    extra = field.field_info.extra
    default_long_arg = "".join([prefix, field_id])

    # If a default value is provided, it's not necessarily required?
    is_required = field.required

    default_value = field.default
    if override_value is not NOT_PROVIDED:
        default_value = override_value
        is_required = False

    try:
        # cli_custom Should be a tuple2[Str, Str]
        cli_custom = __process_tuple(extra["extras"]["cli"], default_long_arg)
    except KeyError:
        if override_cli is None:
            cli_custom = (default_long_arg,)
        else:
            cli_custom = __process_tuple(override_cli, default_long_arg)

    # log.debug(f"Creating Argument Field={field_id} opts:{cli_custom}, default={default_value} type={field.type_} required={is_required} dest={field_id}")

    help_doc = __to_field_description(default_value, field.type_, description)

    parser.add_argument(
        *cli_custom,
        help=help_doc,
        default=default_value,
        dest=field_id,
        required=is_required,
    )

    return parser


def _add_pydantic_class_to_parser(
    p: CustomArgumentParser, cls: BaseModel, default_overrides: T.Dict[T.Text, T.Any]
) -> CustomArgumentParser:

    for ix, field in cls.__fields__.items():

        try:
            default_cli_opts = cls.Config.CLI_EXTRA_OPTIONS[ix]
        except (AttributeError, KeyError):
            default_cli_opts = None

        override_value = default_overrides.get(ix, ...)
        _add_pydantic_field_to_parser(
            p, ix, field, override_value=override_value, override_cli=default_cli_opts
        )

    return p


def pydantic_class_to_parser(
    cls: BaseModel,
    description: T.Optional[T.Text] = None,
    version: T.Optional[T.Text] = None,
    default_value_override=...,
) -> CustomArgumentParser:
    """
    Convert a pydantic data model class to an argparse instance

    :param default_value_override: Is a value provided that will override the default value (if defined)
    in the Pydantic data model class.

    """
    p = CustomArgumentParser(description=description, add_help=False)

    _add_pydantic_class_to_parser(p, cls, default_value_override)

    enable_json, json_key_name = _get_json_config_from_model(cls)

    if enable_json:
        _parser_add_arg_json_file(p, json_key_name)

    _parser_add_help(p)

    if version is not None:
        _parser_add_version(p, version)

    return p


def default_exception_handler(ex) -> int:
    """
    Maps/Transforms the Exception type to an integer exit code
    """
    # this might need the opts instance, however
    # this isn't really well defined if there's an
    # error at that level
    sys.stderr.write(str(ex))
    exc_type, exc_value, exc_traceback = sys.exc_info()
    traceback.print_tb(exc_traceback, file=sys.stderr)
    return 1


def default_epilogue_handler(exit_code: int, run_time_sec: float) -> T.NoReturn:
    """
    General Hook to write that will be executed after the program is
    completed running
    """
    pass


def default_prologue_handler(opts: T.Any) -> T.NoReturn:
    """
    General Hook to call before executing your runner func (e.g., f(opt)).

    Note this is semantically different from what argparse defines as a "prologue".

    This can be used to setup logging.

    :param opts: Will be an instance of your option class
    :return: None
    """
    pass


def _runner(
    args: T.List[T.Text],
    setup_hook: F[[T.List[T.Text]], T.Dict[T.Text, T.Any]],
    to_parser_with_overrides: F[[T.Dict[T.Text, T.Any]], CustomArgumentParser],
    exception_handler,
    prologue_handler,
    epilogue_handler,
) -> int:
    def now():
        return datetime.datetime.now()

    # These initial steps are difficult to debug at times
    # because the logging/prologue hook isn't setup till deep into the
    # steps. This is a bit of bootstrapping problem. You need to parse the
    # config before you setup the prologue_handler/hook.
    started_at = now()
    try:
        # this SHOULD NOT have an "Eager" command defined
        custom_default_values: dict = setup_hook(args)

        # this must already have a closure over the model(s)
        parser: CustomArgumentParser = to_parser_with_overrides(custom_default_values)

        # because of the subparser, the runner func is determined here
        pargs = parser.parse_args(args)

        # this is really only motivated by the subparser case
        # for the simple parser, the Pydantic class could just be passed in
        cls = pargs.cls
        runner_func = pargs.func

        # log.debug(pargs.__dict__)
        opts = cls(**pargs.__dict__)

        # this validation interface is a bit odd
        # and the errors aren't particularly pretty in the console
        cls.validate(opts)
        prologue_handler(opts)
        exit_code = runner_func(opts)
    except TerminalEagerCommand:
        exit_code = 0
    except Exception as e:
        exit_code = exception_handler(e)

    dt = now() - started_at
    epilogue_handler(exit_code, dt.total_seconds())
    # log.debug(f"Completed running in {dt.total_seconds():.4f} sec")
    return exit_code


def null_setup_hook(args: T.List[str]) -> T.Dict[T.Text, T.Any]:
    return {}


def _load_json_file(json_path: str) -> T.Dict[T.Text, T.Any]:
    with open(json_path, "r") as f:
        d = json.load(f)
    return d


def _parser_add_arg_json_file(
    p: CustomArgumentParser, key: str
) -> CustomArgumentParser:
    field = f"--{key}"
    p.add_argument(
        field, default=None, type=str, help="Path to JSON file", required=False
    )
    return p


def to_parser_json_file(json_key_name: str) -> CustomArgumentParser:
    p = CustomArgumentParser(add_help=False)
    _parser_add_arg_json_file(p, json_key_name)
    return p


def setup_hook_to_load_json(
    args: T.List[str], json_config_field_name: str
) -> T.Dict[T.Text, T.Any]:
    # This can't have HelpAction or any other "Eager" action defined
    parser = to_parser_json_file(json_config_field_name)

    # this is a namespace
    pjargs, _ = parser.parse_known_args(args)

    d = {}
    # Argparse will convert "-" to "_" because this dumb Namespace design (which is just a glorified dict)
    sanitized_field_name = json_config_field_name.replace("-", "_")
    json_config_path = getattr(pjargs, sanitized_field_name, None)

    if json_config_path is not None:
        d = _load_json_file(json_config_path)
    # log.debug(f"Loaded custom overrides {d}")
    return d


def _get_json_config_from_model(cls) -> T.Tuple[bool, str]:
    enable_json_config: bool = getattr(
        cls.Config, "CLI_JSON_ENABLE", DefaultConfig.CLI_JSON_ENABLE
    )
    json_key_field_name: str = getattr(
        cls.Config, "CLI_JSON_KEY", DefaultConfig.CLI_JSON_KEY
    )
    return enable_json_config, json_key_field_name


def _runner_with_args(
    args: T.List[T.Text],
    cls: M,
    runner_func: F,
    description: T.Optional[T.Text] = None,
    version: T.Optional[T.Text] = None,
    exception_handler=default_exception_handler,
    prologue_handler: F[[T.Any], T.NoReturn] = default_prologue_handler,
    epilogue_handler: F[[int, float], T.NoReturn] = default_epilogue_handler,
) -> int:
    def to_p(default_override_dict: T.Dict[T.Text, T.Any]) -> CustomArgumentParser:
        # Raw errors at the argparse level aren't always
        # communicated in an obvious way at this level
        parser = pydantic_class_to_parser(
            cls,
            description=description,
            version=version,
            default_value_override=default_override_dict,
        )

        # this is a bit of hackery
        parser.set_defaults(func=runner_func, cls=cls)
        return parser

    enable_json_config, json_key_field_name = _get_json_config_from_model(cls)
    if enable_json_config:

        def __setup(args_):
            return setup_hook_to_load_json(args_, json_key_field_name)

    else:
        __setup = null_setup_hook

    return _runner(
        args, __setup, to_p, exception_handler, prologue_handler, epilogue_handler
    )


def to_runner(
    cls: M,
    runner_func: F,
    description: T.Optional[T.Text] = None,
    version: T.Optional[T.Text] = None,
    exception_handler=default_exception_handler,
    prologue_handler: F[[T.Any], T.NoReturn] = default_prologue_handler,
    epilogue_handler: F[[int, float], T.NoReturn] = default_epilogue_handler,
) -> F[[T.List[T.Text]], int]:
    def f(args: T.List[T.Text]) -> int:
        return _runner_with_args(
            args,
            cls,
            runner_func,
            description=description,
            version=version,
            exception_handler=exception_handler,
            prologue_handler=prologue_handler,
            epilogue_handler=epilogue_handler,
        )

    return f


def run_and_exit(
    cls: M,
    runner_func: F,
    description: T.Optional[T.Text] = None,
    version: T.Optional[T.Text] = None,
    exception_handler=default_exception_handler,
    prologue_handler: F[[T.Any], T.NoReturn] = default_prologue_handler,
    epilogue_handler: F[[int, float], T.NoReturn] = default_epilogue_handler,
    args: T.Optional[T.List[T.Text]] = None,
) -> T.NoReturn:

    _args: T.List[T.Text] = sys.argv[1:] if args is None else args

    sys.exit(
        to_runner(
            cls,
            runner_func,
            description=description,
            version=version,
            exception_handler=exception_handler,
            prologue_handler=prologue_handler,
            epilogue_handler=epilogue_handler,
        )(_args)
    )


def to_subparser(
    models: T.Dict[T.Text, SubParser],
    description: T.Optional[T.Text] = None,
    version: T.Optional[T.Text] = None,
    overrides: T.Optional[T.Dict[T.Text, T.Any]] = None,
) -> ArgumentParser:

    p = ArgumentParser(
        description=description, formatter_class=ArgumentDefaultsHelpFormatter
    )

    # log.debug(f"Creating parser from models {models}")
    sp = p.add_subparsers(
        dest="commands", help="Subparser Commands", parser_class=CustomArgumentParser
    )

    # This fixes an unexpected case where the help isn't called?
    # is this a Py2 to Py3 change?
    sp.required = True
    overrides_defaults = {} if overrides is None else overrides

    for subparser_id, sbm in models.items():
        log.debug(f"Adding subparser id={subparser_id} with {sbm}")

        # I believe mypy is confused by return type
        spx = sp.add_parser(subparser_id, help=sbm.description, add_help=False)

        _add_pydantic_class_to_parser(
            spx, sbm.model_class, default_overrides=overrides_defaults
        )
        enable_json_key, json_key_field_name = _get_json_config_from_model(
            sbm.model_class
        )

        if enable_json_key:
            _parser_add_arg_json_file(spx, json_key_field_name)

        _parser_add_help(spx)

        spx.set_defaults(func=sbm.runner_func, cls=sbm.model_class)

    if version is not None:
        _parser_add_version(p, version)

    return p


def to_runner_sp(
    subparsers: T.Dict[T.Text, SubParser],
    description: T.Optional[T.Text] = None,
    version: T.Optional[T.Text] = None,
    exception_handler: F[[BaseException], int] = default_exception_handler,
    prologue_handler: F[[T.Any], T.NoReturn] = default_prologue_handler,
    epilogue_handler: F[[int, float], T.NoReturn] = default_epilogue_handler,
) -> F[[T.List[T.Text]], int]:

    # This is a bit messy. The design calling _runner requires a single setup hook.
    # in principle, there can be different json key names for each subparser
    # there's not really a clean way to support different key names (which
    # you probably don't want for consistency sake.

    for sbm in subparsers.values():
        enable_json, json_key_name = _get_json_config_from_model(sbm.model_class)

        if enable_json:

            def _setup_hook(args: T.List[T.Text]) -> T.Dict[T.Text, T.Any]:
                return setup_hook_to_load_json(args, json_key_name)

        else:
            _setup_hook = null_setup_hook

    def _to_parser(overrides: T.Dict[T.Text, T.Any]) -> CustomArgumentParser:
        return to_subparser(
            subparsers, description=description, version=version, overrides=overrides
        )

    def f(args: T.List[T.Text]) -> int:
        return _runner(
            args,
            _setup_hook,
            _to_parser,
            exception_handler,
            prologue_handler,
            epilogue_handler,
        )

    return f


def run_sp_and_exit(
    subparsers: T.Dict[T.Text, SubParser],
    description: T.Optional[T.Text] = None,
    version: T.Optional[T.Text] = None,
    exception_handler: F[[BaseException], int] = default_exception_handler,
    prologue_handler: F[[T.Any], T.NoReturn] = default_prologue_handler,
    epilogue_handler: F[[int, float], T.NoReturn] = default_epilogue_handler,
    args=sys.argv[1:],
) -> T.NoReturn:

    f = to_runner_sp(
        subparsers,
        description=description,
        version=version,
        exception_handler=exception_handler,
        prologue_handler=prologue_handler,
        epilogue_handler=epilogue_handler,
    )

    sys.exit(f(args))
