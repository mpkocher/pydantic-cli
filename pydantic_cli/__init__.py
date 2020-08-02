import datetime
import json
import sys
import traceback
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, SUPPRESS, Action
import logging
import typing as T
from typing import Callable as F

from ._version import __version__

from pydantic import BaseModel


log = logging.getLogger(__name__)

NOT_PROVIDED = ...


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

M = T.TypeVar("M", bound=BaseModel)
CustomOptsType = T.Union[T.Tuple[str], T.Tuple[str, str]]
EpilogueHandlerType = F[[int, float], None]
PrologueHandlerType = F[[T.Any], None]
ExceptionHandlerType = F[[BaseException], int]


# This should probably be a concrete datamodel, but it
# wouldn't really work stylistically with how Pydantic's Config
# is defined and "mixed-in"
class DefaultConfig:
    """
    Core Default Config "mixin" for CLI configuration.
    """

    # value used to generate the CLI format --{key}
    CLI_JSON_KEY: str = "json-config"
    # Enable JSON config loading
    CLI_JSON_ENABLE: bool = False
    # Can be used to override custom fields
    # e.g., {"max_records": ('-m', '--max-records')}
    # or {"max_records": ('-m', )}
    CLI_EXTRA_OPTIONS: T.Dict[str, CustomOptsType] = {}

    # Customize the default prefix that is generated
    # if a boolean flag is provided. Boolean custom CLI
    # MUST be provided as Tuple[str, str]
    CLI_BOOL_PREFIX: T.Tuple[str, str] = ("--enable-", "--disable-")


class TerminalEagerCommand(Exception):
    """
    An "Eager" Action (e.g., --version, --help) has completed successfully

    This will be used as a Control structure to deal with the .exit()
    calls that are used on some Actions (e.g., Help, Version)
    """


class FailedExecutionException(Exception):
    def __init__(self, exit_code: int, message: str):
        self.exit_code = exit_code
        self.message = message
        super(FailedExecutionException, self).__init__(self.message)


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
    def exit(self, status: int = 0, message: T.Optional[str] = None) -> T.NoReturn:  # type: ignore
        # THIS IS NO longer used because of the custom Version and Help
        # This is a bit of an issue to return the exit code properly
        # log.debug(f"{self} Class:{self.__class__.__name__} called exit()")
        if status != 0:
            raise FailedExecutionException(
                status, f"Status ({status}) Failed to run command {message}"
            )


class SubParser(T.Generic[M]):
    def __init__(
        self,
        model_class: T.Type[M],
        runner_func: F[[M], int],
        description: T.Optional[str],
    ):
        self.model_class = model_class
        self.runner_func = runner_func
        self.description = description

    def __repr__(self):
        # not every func instance has __name__, e.g., functools.partial
        name = getattr(self.runner_func, "__name__", str(self.runner_func))
        d = dict(k=str(self.model_class), f=name)
        return "<{k} func:{f} >".format(**d)


def _parser_add_help(p: CustomArgumentParser):
    p.add_argument(
        "--help", help="Print Help and Exit", action=EagerHelpAction, default=SUPPRESS
    )
    return p


def _parser_add_version(parser: ArgumentParser, version: str) -> ArgumentParser:
    parser.add_argument("--version", action=EagerVersionAction, version=version)
    return parser


def __try_to_pretty_type(prefix, field_type) -> str:
    """
    This is a marginal improvement to get the types to be
    displayed in slightly better format.

    FIXME. This needs to be display Union types better.
    """
    try:
        sx = field_type.__name__
        return f"{prefix}:{sx}"
    except AttributeError:
        return f"{field_type}"


def __to_field_description(
    default_value=NOT_PROVIDED, field_type=NOT_PROVIDED, description=None
):
    desc = "" if description is None else description
    t = "" if field_type is NOT_PROVIDED else __try_to_pretty_type("type", field_type)
    v = "" if default_value is NOT_PROVIDED else f"default:{default_value}"
    if not (t + v):
        xs = "".join([t, v])
    else:
        xs = " ".join([t, v])
    return f"{desc} ({xs})"


def __process_tuple(
    tuple_one_or_two: T.Sequence[str], long_arg: str
) -> T.Union[T.Tuple[str], T.Tuple[str, str]]:
    """
    If the custom args are provided as only short, then
    add the long version.
    """
    lx: T.List[str] = list(tuple_one_or_two)

    def is_short(xs) -> int:
        # xs = '-s'
        return len(xs) == 2

    nx = len(lx)
    if nx == 1:
        first = lx[0]
        if is_short(first):
            return first, long_arg
        else:
            # this is the positional only case
            return (first,)
    elif len(lx) == 2:
        # the explicit form is provided
        return lx[0], lx[1]
    else:
        raise ValueError(
            f"Unsupported format for `{tuple_one_or_two}`. Expected 1 or 2 tuple."
        )


def __add_boolean_option(
    parser: CustomArgumentParser,
    field_id: str,
    cli_custom: CustomOptsType,
    default_value: bool,
    is_required: bool,
) -> CustomArgumentParser:
    # Overall this is a bit messy to add a boolean flag.

    error_msg = (
        f"boolean field ({field_id}) with custom CLI options ({cli_custom}) must be defined "
        "as a Tuple2[str, str] of True, False for the field. For example, (--enable-X, --disable-X)."
    )

    n = len(cli_custom)

    if n == 2:
        # Argparse is really a thorny beast
        # if you set the group level required=True, then the add_argument must be
        # set to optional (this is encapsulated at the group level). Otherwise
        # argparse will raise "mutually exclusive arguments must be optional"
        group = parser.add_mutually_exclusive_group(required=is_required)
        # log.info(f"Field={field_id}. Creating group {group} required={is_required}")

        # see comments above about Group
        if is_required:
            is_required = False

        bool_datum = [(True, "store_true"), (False, "store_false")]

        for k, (bool_, store_bool) in zip(cli_custom, bool_datum):
            if bool_ != default_value:
                help_ = f"Set {field_id} to {bool_}"
                group.add_argument(
                    k,
                    help=help_,
                    action=store_bool,
                    default=default_value,
                    dest=field_id,
                    required=is_required,
                )
    else:
        raise ValueError(error_msg)

    return parser


def _add_pydantic_field_to_parser(
    parser: CustomArgumentParser,
    field_id: str,
    field,
    override_value: T.Any = ...,
    override_cli: T.Optional[CustomOptsType] = None,
    long_prefix: str = "--",
    bool_prefix: T.Tuple[str, str] = DefaultConfig.CLI_BOOL_PREFIX,
) -> ArgumentParser:
    """

    :param field_id: Global Id used to store
    :param field: Field from Pydantic (this is messy from a type standpoint)
    :param override_value: override the default value defined in the Field
    :param override_cli: Custom format of the CLI argument
    """

    # field is Field from Pydantic
    description = field.field_info.description
    extra: T.Dict[str, T.Any] = field.field_info.extra
    default_long_arg = "".join([long_prefix, field_id])

    # If a default value is provided, it's not necessarily required?
    is_required = field.required

    default_value = field.default
    if override_value is not NOT_PROVIDED:
        default_value = override_value
        is_required = False

    try:
        # cli_custom Should be a tuple2[Str, Str]
        cli_custom: CustomOptsType = __process_tuple(
            extra["extras"]["cli"], default_long_arg
        )
    except KeyError:
        if override_cli is None:
            if field.type_ == bool:
                cli_custom = (
                    f"{bool_prefix[0]}{field_id}",
                    f"{bool_prefix[1]}{field_id}",
                )
            else:
                cli_custom = (default_long_arg,)
        else:
            cli_custom = __process_tuple(override_cli, default_long_arg)

    # log.debug(f"Creating Argument Field={field_id} opts:{cli_custom}, default={default_value} type={field.type_} required={is_required} dest={field_id}")

    help_doc = __to_field_description(default_value, field.type_, description)

    if field.type_ == bool:
        __add_boolean_option(parser, field_id, cli_custom, default_value, is_required)
    else:
        parser.add_argument(
            *cli_custom,
            help=help_doc,
            default=default_value,
            dest=field_id,
            required=is_required,
        )

    return parser


def _add_pydantic_class_to_parser(
    p: CustomArgumentParser, cls: T.Type[M], default_overrides: T.Dict[str, T.Any]
) -> CustomArgumentParser:

    for ix, field in cls.__fields__.items():

        dx = getattr(cls.Config, "CLI_EXTRA_OPTIONS", DefaultConfig.CLI_EXTRA_OPTIONS)
        default_cli_opts: T.Optional[CustomOptsType] = dx.get(ix, None)
        custom_bool_prefix = getattr(
            cls.Config, "CLI_BOOL_PREFIX", DefaultConfig.CLI_BOOL_PREFIX
        )

        override_value = default_overrides.get(ix, ...)
        _add_pydantic_field_to_parser(
            p,
            ix,
            field,
            override_value=override_value,
            override_cli=default_cli_opts,
            bool_prefix=custom_bool_prefix,
        )

    return p


def pydantic_class_to_parser(
    cls: T.Type[M],
    description: T.Optional[str] = None,
    version: T.Optional[str] = None,
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


def _get_error_exit_code(ex: BaseException, default_exit_code: int = 1) -> int:
    if isinstance(ex, FailedExecutionException):
        exit_code = ex.exit_code
    else:
        exit_code = default_exit_code
    return exit_code


def default_exception_handler(ex: BaseException) -> int:
    """
    Maps/Transforms the Exception type to an integer exit code
    """
    # this might need the opts instance, however
    # this isn't really well defined if there's an
    # error at that level
    sys.stderr.write(str(ex))
    exc_type, exc_value, exc_traceback = sys.exc_info()
    traceback.print_tb(exc_traceback, file=sys.stderr)
    return _get_error_exit_code(ex, 1)


def default_minimal_exception_handler(ex: BaseException) -> int:
    """
    Only write a terse error message. Don't output the entire stacktrace
    """
    sys.stderr.write(str(ex))
    return _get_error_exit_code(ex, 1)


def default_epilogue_handler(exit_code: int, run_time_sec: float) -> None:
    """
    General Hook to write that will be executed after the program is
    completed running
    """
    pass


def default_prologue_handler(opts: T.Any) -> None:
    """
    General Hook to call before executing your runner func (e.g., f(opt)).

    Note this is semantically different from what argparse defines as a "prologue".

    This can be used to setup logging.

    :param opts: Will be an instance of your option class
    :return: None
    """
    pass


def _runner(
    args: T.List[str],
    setup_hook: F[[T.List[str]], T.Dict[str, T.Any]],
    to_parser_with_overrides: F[[T.Dict[str, T.Any]], CustomArgumentParser],
    exception_handler: ExceptionHandlerType,
    prologue_handler: PrologueHandlerType,
    epilogue_handler: EpilogueHandlerType,
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
        # There's some slop in here using set_default(func=) hack/trick
        # hence we have to explictly define the expected type
        runner_func: F[[T.Any], int] = pargs.func

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


def null_setup_hook(args: T.List[str]) -> T.Dict[str, T.Any]:
    return {}


def _load_json_file(json_path: str) -> T.Dict[str, T.Any]:
    with open(json_path, "r") as f:
        d: T.Dict[str, T.Any] = json.load(f)
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
) -> T.Dict[str, T.Any]:
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
    args: T.List[str],
    cls: T.Type[M],
    runner_func: F[[M], int],
    description: T.Optional[str] = None,
    version: T.Optional[str] = None,
    exception_handler: ExceptionHandlerType = default_exception_handler,
    prologue_handler: PrologueHandlerType = default_prologue_handler,
    epilogue_handler: EpilogueHandlerType = default_epilogue_handler,
) -> int:
    def to_p(default_override_dict: T.Dict[str, T.Any]) -> CustomArgumentParser:
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


class to_runner(T.Generic[M]):
    """
    This is written as a class instead of simple function to get the Parametric Polymorphism to work correctly.
    """

    def __init__(
        self,
        cls: T.Type[M],
        runner_func: F[[M], int],
        description: T.Optional[str] = None,
        version: T.Optional[str] = None,
        exception_handler: ExceptionHandlerType = default_exception_handler,
        prologue_handler: PrologueHandlerType = default_prologue_handler,
        epilogue_handler: EpilogueHandlerType = default_epilogue_handler,
    ):
        self.cls = cls
        self.runner_func = runner_func
        self.description = description
        self.version = version
        self.exception_handler = exception_handler
        self.prologue_handler = prologue_handler
        self.epilogue_handler = epilogue_handler

    def __call__(self, args: T.List[str]) -> int:
        return _runner_with_args(
            args,
            self.cls,
            self.runner_func,
            description=self.description,
            version=self.version,
            exception_handler=self.exception_handler,
            prologue_handler=self.prologue_handler,
            epilogue_handler=self.epilogue_handler,
        )


def run_and_exit(
    cls: T.Type[M],
    runner_func: F[[M], int],
    description: T.Optional[str] = None,
    version: T.Optional[str] = None,
    exception_handler: ExceptionHandlerType = default_exception_handler,
    prologue_handler: PrologueHandlerType = default_prologue_handler,
    epilogue_handler: EpilogueHandlerType = default_epilogue_handler,
    args: T.Optional[T.List[str]] = None,
) -> T.NoReturn:

    _args: T.List[str] = sys.argv[1:] if args is None else args

    sys.exit(
        to_runner[M](
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
    models: T.Dict[str, SubParser],
    description: T.Optional[str] = None,
    version: T.Optional[str] = None,
    overrides: T.Optional[T.Dict[str, T.Any]] = None,
) -> CustomArgumentParser:

    p = CustomArgumentParser(
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
        spx = T.cast(
            CustomArgumentParser,
            sp.add_parser(subparser_id, help=sbm.description, add_help=False),
        )

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
    subparsers: T.Dict[str, SubParser],
    description: T.Optional[str] = None,
    version: T.Optional[str] = None,
    exception_handler: ExceptionHandlerType = default_exception_handler,
    prologue_handler: PrologueHandlerType = default_prologue_handler,
    epilogue_handler: EpilogueHandlerType = default_epilogue_handler,
) -> F[[T.List[str]], int]:

    # This is a bit messy. The design calling _runner requires a single setup hook.
    # in principle, there can be different json key names for each subparser
    # there's not really a clean way to support different key names (which
    # you probably don't want for consistency sake.

    for sbm in subparsers.values():
        enable_json, json_key_name = _get_json_config_from_model(sbm.model_class)

        if enable_json:

            def _setup_hook(args: T.List[str]) -> T.Dict[str, T.Any]:
                return setup_hook_to_load_json(args, json_key_name)

        else:
            _setup_hook = null_setup_hook

    def _to_parser(overrides: T.Dict[str, T.Any]) -> CustomArgumentParser:
        return to_subparser(
            subparsers, description=description, version=version, overrides=overrides
        )

    def f(args: T.List[str]) -> int:
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
    subparsers: T.Dict[str, SubParser[M]],
    description: T.Optional[str] = None,
    version: T.Optional[str] = None,
    exception_handler: ExceptionHandlerType = default_exception_handler,
    prologue_handler: PrologueHandlerType = default_prologue_handler,
    epilogue_handler: EpilogueHandlerType = default_epilogue_handler,
    args: T.Optional[T.List[str]] = None,
) -> T.NoReturn:

    f = to_runner_sp(
        subparsers,
        description=description,
        version=version,
        exception_handler=exception_handler,
        prologue_handler=prologue_handler,
        epilogue_handler=epilogue_handler,
    )

    _args: T.List[str] = sys.argv[1:] if args is None else args
    sys.exit(f(_args))
