import abc
import collections
import datetime
import sys
import traceback
import logging
import typing
from copy import deepcopy
from typing import overload
from typing import Any, Mapping, Callable


import pydantic
from pydantic import BaseModel
from pydantic.fields import FieldInfo

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


__all__ = [
    "Cmd",
    "to_runner",
    "run_and_exit",
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


class Cmd(BaseModel):
    @abc.abstractmethod
    def run(self) -> None: ...


CmdKlassT = type[Cmd]
SubCmdKlassT = Mapping[str, CmdKlassT]
CmdOrSubCmdKlassT = CmdKlassT | SubCmdKlassT
NOT_PROVIDED = ...


def _is_sequence(annotation: Any) -> bool:
    #  FIXME There's probably a better and robust way to do this.
    # Lifted from pydantic
    LIST_TYPES: list[type] = [list, typing.List, collections.abc.MutableSequence]
    SET_TYPES: list[type] = [set, typing.Set, collections.abc.MutableSet]
    FROZEN_SET_TYPES: list[type] = [frozenset, typing.FrozenSet, collections.abc.Set]
    ALL_SEQ = set(LIST_TYPES + SET_TYPES + FROZEN_SET_TYPES)

    # what is exactly going on here?
    return getattr(annotation, "__origin__", "NOTFOUND") in ALL_SEQ


@pydantic.validate_call
def __process_tuple(tuple_one_or_two: Tuple1or2Type, long_arg: str) -> Tuple1or2Type:
    """
    If the custom args are provided as only short, then
    add the long version. Or just use the
    """
    lx: list[str] = list(tuple_one_or_two)

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
    override_value: Any = ...,
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
    # there's mypy type issues here
    cli_custom_: Tuple1or2Type = (
        (default_long_arg,)
        if field_info.json_schema_extra is None  # type: ignore
        else field_info.json_schema_extra.get("cli", (default_long_arg,))  # type: ignore
    )
    cli_short_long: Tuple1or2Type = __process_tuple(cli_custom_, default_long_arg)

    is_required = field_info.is_required()
    default_value = field_info.default
    is_sequence = _is_sequence(field_info.annotation)

    # If the value is loaded from JSON, or ENV, this will fundamentally
    # change if a field is required.
    if override_value is not NOT_PROVIDED:
        default_value = override_value
        is_required = False

    # Delete cli and json_schema_extras metadata isn't in FieldInfo and won't be displayed
    # Not sure if this is the correct, or expected behavior.
    cfield_info = deepcopy(field_info)
    cfield_info.json_schema_extra = None
    # write this to keep backward compat with 3.10
    help_ = "".join(["Field(", field_info.__repr_str__(", "), ")"])

    # log.debug(f"Creating Argument Field={field_id} opts:{cli_short_long}, allow_none={field.allow_none} default={default_value} type={field.type_} required={is_required} dest={field_id} desc={description}")

    # MK. I don't think there's any point trying to fight with argparse to get
    # the types correct here. It's just a mess from a type standpoint.
    shape_kw = {"nargs": "+"} if is_sequence else {}
    parser.add_argument(
        *cli_short_long,
        help=help_,
        default=default_value,
        dest=field_id,
        required=is_required,
        **shape_kw,  # type: ignore
    )

    return parser


def _add_pydantic_class_to_parser(
    p: CustomArgumentParser, cmd: CmdKlassT, default_overrides: dict[str, Any]
) -> CustomArgumentParser:

    for ix, field in cmd.model_fields.items():
        override_value = default_overrides.get(ix, ...)
        _add_pydantic_field_to_parser(p, ix, field, override_value=override_value)

    return p


def pydantic_class_to_parser(
    cls: CmdKlassT,
    description: str | None = None,
    version: str | None = None,
    default_value_override: Any = NOT_PROVIDED,
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


def default_prologue_handler(opts: Any) -> None:
    """
    General Hook to call before executing your runner func (e.g., f(opt)).

    Note this is semantically different from what argparse defines as a "prologue".

    This can be used to setup logging.

    :param opts: Will be an instance of your option class
    :return: None
    """
    pass


def _runner(
    args: list[str],
    setup_hook: Callable[[list[str]], dict[str, Any]],
    to_parser_with_overrides: Callable[[dict[str, Any]], CustomArgumentParser],
    exception_handler: ExceptionHandlerType,
    prologue_handler: PrologueHandlerType,
    epilogue_handler: EpilogueHandlerType,
) -> int:
    """
    This is the fundamental hook into orchestrating the processing of the
    supplied commandline args.
    """

    def now() -> datetime.datetime:
        return datetime.datetime.now()

    # These initial steps are difficult to debug at times
    # because the logging/prologue hook isn't setup till deep into the
    # steps. This is a bit of bootstrapping problem. You need to parse the
    # config before you setup the prologue_handler/hook.
    started_at = now()
    try:
        # this SHOULD NOT have an "Eager" command defined
        custom_default_values: dict[str, Any] = setup_hook(args)

        # this must already have a closure over the model(s)
        parser: CustomArgumentParser = to_parser_with_overrides(custom_default_values)

        # because of the subparser, the runner func is determined here
        pargs = parser.parse_args(args)

        # this is really only motivated by the subparser case
        # for the simple parser, the Pydantic class could just be passed in
        cmd_cls: type[Cmd] = pargs.cmd
        # There's some slop in here using set_default(func=) hack/trick

        # log.debug(pargs.__dict__)
        d = pargs.__dict__

        # This is a bit sloppy. There's some fields that are added
        # to the argparse namespace to get around some of argparse's thorny design
        pure_keys = cmd_cls.model_json_schema()["properties"].keys()

        # Remove the items that may have
        # polluted the namespace (e.g., func, cls, json_config)
        # to avoid leaking into the Pydantic data model.
        pure_d = {k: v for k, v in d.items() if k in pure_keys}

        cmd = cmd_cls(**pure_d)

        # this validation interface is a bit odd
        # and the errors aren't particularly pretty in the console
        cmd_cls.model_validate(cmd)
        prologue_handler(cmd)
        # This should raise if there's an issue
        out = cmd.run()
        if out is not None:
            log.warning("Cmd.run() should return None or raise an exception.")
        exit_code = 0
    except TerminalEagerCommand:
        exit_code = 0
    except Exception as e:
        exit_code = exception_handler(e)

    dt = now() - started_at
    epilogue_handler(exit_code, dt.total_seconds())
    # log.debug(f"Completed running in {dt.total_seconds():.4f} sec")
    return exit_code


def null_setup_hook(args: list[str]) -> dict[str, Any]:
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


def setup_hook_to_load_json(args: list[str], cli_config: CliConfig) -> dict[str, Any]:

    # This can't have HelpAction or any other "Eager" action defined
    parser = create_parser_with_config_json_file_arg(cli_config)

    # this is a namespace
    pjargs, _ = parser.parse_known_args(args)

    d = {}

    #  Arg parse will do some munging on this due to its Namespace attribute style.
    json_config_path = getattr(
        pjargs, cli_config["cli_json_key"].replace("-", "_"), None
    )

    if json_config_path is not None:
        d = _load_json_file(json_config_path)
    # log.debug(f"Loaded custom overrides {d}")
    return d


def _to_runner_with_args(
    cmd: CmdKlassT,
    *,
    description: str | None = None,
    version: str | None = None,
    exception_handler: ExceptionHandlerType = default_exception_handler,
    prologue_handler: PrologueHandlerType = default_prologue_handler,
    epilogue_handler: EpilogueHandlerType = default_epilogue_handler,
) -> Callable[[list[str]], int]:
    def to_p(default_override_dict: dict[str, Any]) -> CustomArgumentParser:
        # Raw errors at the argparse level aren't always
        # communicated in an obvious way at this level
        parser = pydantic_class_to_parser(
            cmd,
            description=description,
            version=version,
            default_value_override=default_override_dict,
        )

        # call opts.run() downstream
        parser.set_defaults(cmd=cmd)
        return parser

    cli_config = _get_cli_config_from_model(cmd)

    if cli_config["cli_json_enable"]:

        def __setup(args: list[str]) -> dict[str, Any]:
            c = cli_config.copy()
            c["cli_json_validate_path"] = False
            return setup_hook_to_load_json(args, c)

    else:
        __setup = null_setup_hook

    def f(args: list[str]) -> int:
        return _runner(
            args, __setup, to_p, exception_handler, prologue_handler, epilogue_handler
        )

    return f


def _to_subparser(
    cmds: SubCmdKlassT,
    *,
    description: str | None = None,
    version: str | None = None,
    overrides: dict[str, Any] | None = None,
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

    for subparser_id, cmd in cmds.items():
        log.debug(f"Adding subparser id={subparser_id} with {cmd}")

        spx: CustomArgumentParser = sp.add_parser(
            subparser_id, help=cmd.__doc__, add_help=False
        )

        _add_pydantic_class_to_parser(spx, cmd, default_overrides=overrides_defaults)

        cli_config = _get_cli_config_from_model(cmd)

        if cli_config["cli_json_enable"]:
            _parser_add_arg_json_file(spx, cli_config)

        _parser_add_help(spx)

        spx.set_defaults(cmd=cmd)

    if version is not None:
        _parser_add_version(p, version)

    return p


def _to_runner_sp_with_args(
    cmds: SubCmdKlassT,
    *,
    description: str | None = None,
    version: str | None = None,
    exception_handler: ExceptionHandlerType = default_exception_handler,
    prologue_handler: PrologueHandlerType = default_prologue_handler,
    epilogue_handler: EpilogueHandlerType = default_epilogue_handler,
) -> Callable[[list[str]], int]:

    # This is a bit messy. The design calling _runner requires a single setup hook.
    # in principle, there can be different json key names for each subparser
    # there's not really a clean way to support different key names (which
    # you probably don't want for consistency’s sake.

    for cmd in cmds.values():
        cli_config = _get_cli_config_from_model(cmd)

        if cli_config["cli_json_enable"]:

            def _setup_hook(args: list[str]) -> dict[str, Any]:
                # We allow the setup to fail if the JSON config isn't found
                c = cli_config.copy()
                c["cli_json_validate_path"] = False
                return setup_hook_to_load_json(args, cli_config)

        else:
            _setup_hook = null_setup_hook

    def _to_parser(overrides: dict[str, Any]) -> CustomArgumentParser:
        return _to_subparser(
            cmds, description=description, version=version, overrides=overrides
        )

    def f(args: list[str]) -> int:
        return _runner(
            args,
            _setup_hook,
            _to_parser,
            exception_handler,
            prologue_handler,
            epilogue_handler,
        )

    return f


@overload
def to_runner(
    xs: CmdKlassT,
    *,
    description: str | None = None,
    version: str | None = None,
    exception_handler: ExceptionHandlerType = default_exception_handler,
    prologue_handler: PrologueHandlerType = default_prologue_handler,
    epilogue_handler: EpilogueHandlerType = default_epilogue_handler,
) -> Callable[[list[str]], int]: ...


@overload
def to_runner(
    xs: SubCmdKlassT,
    *,
    description: str | None = None,
    version: str | None = None,
    exception_handler: ExceptionHandlerType = default_exception_handler,
    prologue_handler: PrologueHandlerType = default_prologue_handler,
    epilogue_handler: EpilogueHandlerType = default_epilogue_handler,
) -> Callable[[list[str]], int]: ...


def to_runner(
    xs: CmdOrSubCmdKlassT,
    *,
    description: str | None = None,
    version: str | None = None,
    exception_handler: ExceptionHandlerType = default_exception_handler,
    prologue_handler: PrologueHandlerType = default_prologue_handler,
    epilogue_handler: EpilogueHandlerType = default_epilogue_handler,
) -> Callable[[list[str]], int]:
    """
    Core method to return a func(list[str]) -> int
    """

    # FIXME. This runtime type checking should be more strict
    # explicitly writing these out in each if block to avoid
    # friction points with mypy.
    if isinstance(xs, type(Cmd)):
        return _to_runner_with_args(
            xs,
            description=description,
            version=version,
            exception_handler=exception_handler,
            prologue_handler=prologue_handler,
            epilogue_handler=epilogue_handler,
        )
    elif isinstance(xs, dict):
        return _to_runner_sp_with_args(
            xs,
            description=description,
            version=version,
            exception_handler=exception_handler,
            prologue_handler=prologue_handler,
            epilogue_handler=epilogue_handler,
        )
    else:
        raise ValueError(f"Invalid cmd {xs}")


@overload
def run_and_exit(
    xs: CmdKlassT,
    *,
    description: str | None = None,
    version: str | None = None,
    exception_handler: ExceptionHandlerType = default_exception_handler,
    prologue_handler: PrologueHandlerType = default_prologue_handler,
    epilogue_handler: EpilogueHandlerType = default_epilogue_handler,
    args: list[str] | None = None,
) -> typing.NoReturn: ...


@overload
def run_and_exit(
    xs: SubCmdKlassT,
    *,
    description: str | None = None,
    version: str | None = None,
    exception_handler: ExceptionHandlerType = default_exception_handler,
    prologue_handler: PrologueHandlerType = default_prologue_handler,
    epilogue_handler: EpilogueHandlerType = default_epilogue_handler,
    args: list[str] | None = None,
) -> typing.NoReturn: ...


def run_and_exit(
    xs: CmdOrSubCmdKlassT,
    *,
    description: str | None = None,
    version: str | None = None,
    exception_handler: ExceptionHandlerType = default_exception_handler,
    prologue_handler: PrologueHandlerType = default_prologue_handler,
    epilogue_handler: EpilogueHandlerType = default_epilogue_handler,
    args: list[str] | None = None,
) -> typing.NoReturn:

    f = to_runner(
        xs,
        description=description,
        version=version,
        exception_handler=exception_handler,
        prologue_handler=prologue_handler,
        epilogue_handler=epilogue_handler,
    )

    _args: list[str] = sys.argv[1:] if args is None else args
    sys.exit(f(_args))
