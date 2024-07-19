import collections
import datetime
import sys
import traceback
import logging
import typing
import typing as T
from typing import Callable as F

import pydantic
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

from ._version import __version__

from .core import M, Tuple1or2Type, Tuple1Type, Tuple2Type
from .core import EpilogueHandlerType, PrologueHandlerType, ExceptionHandlerType
from .core import (
    CliConfig,
    _get_cli_config_from_model,
)
from .utils import _load_json_file, _resolve_file, _resolve_file_or_none_and_warn
from .argparse import CustomArgumentParser, EagerHelpAction
from .argparse import _parser_add_help, _parser_add_version
from .argparse import FailedExecutionException, TerminalEagerCommand
from argparse import ArgumentDefaultsHelpFormatter
from .shell_completion import (
    EmitShellCompletionAction,
    add_shell_completion_arg,
    HAS_AUTOCOMPLETE_SUPPORT,
)

log = logging.getLogger(__name__)

NOT_PROVIDED = ...
NONE_TYPE = type(None)

__all__ = [
    "to_runner",
    "run_and_exit",
    "to_runner_sp",
    "run_sp_and_exit",
    "default_exception_handler",
    "default_minimal_exception_handler",
    "default_prologue_handler",
    "default_epilogue_handler",
    "CliConfig",
    "HAS_AUTOCOMPLETE_SUPPORT",
    "PrologueHandlerType",
    "EpilogueHandlerType",
    "__version__",
]


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


def _is_sequence(annotation: T.Any) -> bool:
    #  FIXME There's probably a better and robust way to do this.
    # Lifted from pydantic
    LIST_TYPES: list[type] = [list, typing.List, collections.abc.MutableSequence]
    SET_TYPES: list[type] = [set, typing.Set, collections.abc.MutableSet]
    FROZEN_SET_TYPES: list[type] = [frozenset, typing.FrozenSet, collections.abc.Set]
    ALL_SEQ = set(LIST_TYPES + SET_TYPES + FROZEN_SET_TYPES)

    # what is exactly going on here?
    return getattr(annotation, "__origin__", "NOTFOUND") in ALL_SEQ


def __try_to_pretty_type(field_type) -> str:
    """
    This is a marginal improvement to get the types to be
    displayed in slightly better format.

    FIXME. This needs to be display Union types better.
    """

    args = typing.get_args(field_type)
    if args:
        if len(args) == 1:
            name = field_type.__name__
        else:
            name = "|".join(map(lambda x: x.__name__, args))
    else:
        try:
            name = field_type.__name__
        except AttributeError:
            name = repr(field_type)

    return f"type:{name}"


def __to_type_description(
    default_value=NOT_PROVIDED,
    field_type=NOT_PROVIDED,
    allow_none: bool = False,
    is_required: bool = False,
):
    t = "" if field_type is NOT_PROVIDED else __try_to_pretty_type(field_type)
    # FIXME Pydantic has a very odd default of None, which makes often can make the
    # the "default" is actually None, or is not None
    # avoid using in with a Set to avoid assumptions that default_value is hashable
    allowed_defaults: T.List[T.Any] = (
        [NOT_PROVIDED, PydanticUndefined]
        if allow_none
        else [NOT_PROVIDED, PydanticUndefined, None, type(None)]
    )
    v = (
        ""
        if any((default_value is x) for x in allowed_defaults)
        else f"default:{default_value}"
    )
    required = " *required*" if is_required else ""
    sep = " " if v else ""
    xs = sep.join([t, v]) + required
    return xs


@pydantic.validate_call
def __process_tuple(tuple_one_or_two: Tuple1or2Type, long_arg: str) -> Tuple1or2Type:
    """
    If the custom args are provided as only short, then
    add the long version. Or just use the
    """
    lx: T.List[str] = list(tuple_one_or_two)

    nx = len(lx)
    if nx == 1:
        if len(lx[0]) == 2:  # xs = '-s'
            return lx[0], long_arg
        else:
            # this is the positional only case
            return (lx[0],)
    elif nx == 2:
        # the explicit form is provided
        return lx[0], lx[1]
    else:
        raise ValueError(
            f"Unsupported format for `{tuple_one_or_two}` type={type(tuple_one_or_two)}. Expected 1 or 2 tuple."
        )


def _add_pydantic_field_to_parser(
    parser: CustomArgumentParser,
    field_id: str,
    field_info: FieldInfo,
    override_value: T.Any = ...,
    long_prefix: str = "--",
) -> CustomArgumentParser:
    """

    :param field_id: Global Id used to store
    :param field_info: FieldInfo from Pydantic (this is messy from a type standpoint)
    :param override_value: override the default value defined in the Field (perhaps define in ENV or JSON file)

    Supported Core cases of primitive types, T (e.g., float, str, int)

    alpha: str                         -> *required* --alpha abc
    alpha: Optional[str]               -> *required* --alpha None  # This is kinda a problem and not well-defined
    alpha: Optional[str] = None        ->            --alpha abc ,or --alpha None (to explicitly set none)

    alpha: bool                        -> *required* --alpha "true" (Pydantic will handle the casting)
    alpha: Optional[bool]              -> *required* --alpha "none" or --alpha true
    alpha: Optional[bool] = True       ->            --alpha "none" or --alpha true


    Sequence Types:

    xs: List[str]                      -> *required* --xs 1 2 3
    xs: Optional[List[str]]            -> There's a useful reason to encode this type, however,
                                          it's not well-defined or supported. This should be List[T]
    """

    default_long_arg = "".join([long_prefix, field_id])
    description = field_info.description
    # there's mypy type issues here
    cli_custom_: Tuple1or2Type = (
        (default_long_arg,)
        if field_info.json_schema_extra is None  # type: ignore
        else field_info.json_schema_extra.get("cli", (default_long_arg,))  # type: ignore
    )
    cli_short_long: Tuple1or2Type = __process_tuple(cli_custom_, default_long_arg)

    is_required = field_info.is_required()
    is_nullable = type(None) in typing.get_args(field_info.annotation)
    default_value = field_info.default
    is_sequence = _is_sequence(field_info.annotation)

    # If the value is loaded from JSON, or ENV, this will fundamentally
    # change if a field is required.
    if override_value is not NOT_PROVIDED:
        default_value = override_value
        is_required = False

    type_desc = __to_type_description(
        default_value, field_info.annotation, is_nullable, is_required
    )

    # log.debug(f"Creating Argument Field={field_id} opts:{cli_short_long}, allow_none={field.allow_none} default={default_value} type={field.type_} required={is_required} dest={field_id} desc={description}")

    # MK. I don't think there's any point trying to fight with argparse to get
    # the types correct here. It's just a mess from a type standpoint.
    shape_kw = {"nargs": "+"} if is_sequence else {}
    desc = description or ""
    parser.add_argument(
        *cli_short_long,
        help=f"{desc} ({type_desc})",
        default=default_value,
        dest=field_id,
        required=is_required,
        **shape_kw,  # type: ignore
    )

    return parser


def _add_pydantic_class_to_parser(
    p: CustomArgumentParser, cls: T.Type[M], default_overrides: T.Dict[str, T.Any]
) -> CustomArgumentParser:

    for ix, field in cls.model_fields.items():
        override_value = default_overrides.get(ix, ...)
        _add_pydantic_field_to_parser(p, ix, field, override_value=override_value)

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
    p0 = CustomArgumentParser(description=description, add_help=False)

    p = _add_pydantic_class_to_parser(p0, cls, default_value_override)

    cli_config = _get_cli_config_from_model(cls)

    if cli_config["cli_json_enable"]:
        _parser_add_arg_json_file(p, cli_config)

    if cli_config["cli_shell_completion_enable"]:
        add_shell_completion_arg(p, cli_config["cli_shell_completion_flag"])

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
    # this isn't really well-defined if there's an
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
    """
    This is the fundamental hook into orchestrating the processing of the
    supplied commandline args.
    """

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
        # hence we have to explicitly define the expected type
        runner_func: F[[T.Any], int] = pargs.func

        # log.debug(pargs.__dict__)
        d = pargs.__dict__

        # This is a bit sloppy. There's some fields that are added
        # to the argparse namespace to get around some of argparse's thorny design
        pure_keys = cls.model_json_schema()["properties"].keys()

        # Remove the items that may have
        # polluted the namespace (e.g., func, cls, json_config)
        # to avoid leaking into the Pydantic data model.
        pure_d = {k: v for k, v in d.items() if k in pure_keys}

        opts = cls(**pure_d)

        # this validation interface is a bit odd
        # and the errors aren't particularly pretty in the console
        cls.model_validate(opts)
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


def _parser_add_arg_json_file(
    p: CustomArgumentParser, cli_config: CliConfig
) -> CustomArgumentParser:

    validator = (
        _resolve_file
        if cli_config["cli_json_validate_path"]
        else _resolve_file_or_none_and_warn
    )
    field = f"--{cli_config['cli_json_key']}"

    path = cli_config["cli_json_config_path"]

    help = f"Path to configuration JSON file. Can be set using ENV VAR ({cli_config['cli_json_config_env_var']}) (default:{path})"

    p.add_argument(
        field,
        default=path,
        type=validator,
        help=help,
        required=False,
    )
    return p


def create_parser_with_config_json_file_arg(
    cli_config: CliConfig,
) -> CustomArgumentParser:
    p = CustomArgumentParser(add_help=False)
    _parser_add_arg_json_file(p, cli_config)
    return p


def setup_hook_to_load_json(
    args: T.List[str], cli_config: CliConfig
) -> T.Dict[str, T.Any]:

    # This can't have HelpAction or any other "Eager" action defined
    parser = create_parser_with_config_json_file_arg(cli_config)

    # this is a namespace
    pjargs, _ = parser.parse_known_args(args)

    d = {}

    #  Arg parse will do some munging on this due to it's Namespace attribute style.
    json_config_path = getattr(
        pjargs, cli_config["cli_json_key"].replace("-", "_"), None
    )

    if json_config_path is not None:
        d = _load_json_file(json_config_path)
    # log.debug(f"Loaded custom overrides {d}")
    return d


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

    cli_config = _get_cli_config_from_model(cls)

    if cli_config["cli_json_enable"]:

        def __setup(args: list[str]) -> T.Dict[str, T.Any]:
            c = cli_config.copy()
            c["cli_json_validate_path"] = False
            return setup_hook_to_load_json(args, c)

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

        spx: CustomArgumentParser = sp.add_parser(
            subparser_id, help=sbm.description, add_help=False
        )

        _add_pydantic_class_to_parser(
            spx, sbm.model_class, default_overrides=overrides_defaults
        )

        cli_config = _get_cli_config_from_model(sbm.model_class)

        if cli_config["cli_json_enable"]:
            _parser_add_arg_json_file(spx, cli_config)

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
    # you probably don't want for consistency’s sake.

    for sbm in subparsers.values():
        cli_config = _get_cli_config_from_model(sbm.model_class)

        if cli_config["cli_json_enable"]:

            def _setup_hook(args: T.List[str]) -> T.Dict[str, T.Any]:
                # We allow the setup to fail if the JSON config isn't found
                c = cli_config.copy()
                c["cli_json_validate_path"] = False
                return setup_hook_to_load_json(args, cli_config)

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
