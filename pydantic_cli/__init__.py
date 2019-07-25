import datetime
import sys
import traceback
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import logging
import typing as T


from pydantic import BaseModel

log = logging.getLogger(__name__)

NOT_PROVIDED = object()

VERSION = (0, 4, 0)

__version__ = ".".join([str(i) for i in VERSION])

__all__ = ['to_runner', 'run_and_exit',
           'to_runner_sp', 'run_sp_and_exit',
           'default_exception_handler', 'default_epilogue_handler']


class SubParser(T.NamedTuple):
    options: T.Any
    runner_func: T.Callable
    description: T.Optional[T.AnyStr]


def _parser_add_version(parser: ArgumentParser, version: T.AnyStr) -> ArgumentParser:
    parser.add_argument("--version", action="version", version=version)
    return parser


def __to_field_description(default_value=NOT_PROVIDED, field_type=NOT_PROVIDED, description=None):
    desc = "" if description is None else description
    t = "" if field_type is NOT_PROVIDED else f"type:{field_type}"
    v = "" if default_value is NOT_PROVIDED else f"default:{default_value}"
    if not (t + v):
        xs = "".join([t, v])
    else:
        xs = " ".join([t, v])
    return f"{desc} ({xs})"


def __process_tuple(tuple_one_or_two, long_arg):
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


def _add_pydantic_field_to_parser(p, ix, field, override_cli=None) -> ArgumentParser:

    schema = field.schema
    default_long_arg = f"--{ix}"

    is_positional = field.required

    # Should be a tuple2[Str, Str]
    try:
        cli_custom = __process_tuple(schema.extra['extras']['cli'], default_long_arg)
        is_positional = False
    except KeyError:
        if override_cli is None:
            if is_positional:
                cli_custom = (ix, )
            else:
                cli_custom = (default_long_arg, )
        else:
            cli_custom = __process_tuple(override_cli, default_long_arg)

    log.debug(f"Creating Argument with opts:{cli_custom}, default={field.default} type={field.type_} positional={is_positional} required={field.required}")

    f = __to_field_description
    # this API is so thorny to code around. if dest='x' and p.add_argument('x') will raise
    if is_positional:
        p.add_argument(*cli_custom, help=f(NOT_PROVIDED, field.type_, schema.description), default=field.default)
    else:
        p.add_argument(*cli_custom, help=f(field.default, field.type_, schema.description), default=field.default, dest=ix, required=field.required)
    return p


def _add_pydantic_class_to_parser(p, cls) -> ArgumentParser:

    for ix, field in cls.__fields__.items():

        try:
            default_cli_opts = cls.Config.CLI_EXTRA_OPTIONS[ix]
        except (AttributeError, KeyError):
            default_cli_opts = None

        _add_pydantic_field_to_parser(p, ix, field,
                                      override_cli=default_cli_opts)

    return p


def pydantic_class_to_parser(cls, description=None, version=None) -> ArgumentParser:
    """
    Convert a pydantic data model class to an argparse instance
    """
    # Is there really not a lib for a JsonSchema Property to argparse option?

    p = ArgumentParser(description=description)

    _add_pydantic_class_to_parser(p, cls)

    if version is not None:
        _parser_add_version(p, version)

    return p


def default_exception_handler(ex) -> int:
    # this might need the opts instance, however
    # this isn't really well defined if there's an
    # error at that level
    sys.stderr.write(str(ex))
    exc_type, exc_value, exc_traceback = sys.exc_info()
    traceback.print_tb(exc_traceback, file=sys.stderr)
    return 1


def default_epilogue_handler(exit_code: int, run_time_sec: float):
    """
    General Hook to write that will be executed after the program is
    completed running
    """
    pass


def _runner(args, parser:ArgumentParser, exception_handler, epilogue_handler) -> int:

    def now():
        return datetime.datetime.now()

    started_at = now()
    try:
        # this is a really lackluster design
        # any --version or --help has sys.exit call
        # that is triggered from parser.exit()
        pargs = parser.parse_args(args)

        # This hackery is required for subparser case
        if not hasattr(pargs, 'cls'):
            parser.print_usage()
            parser.exit(1)

        cls = pargs.cls
        runner_func = pargs.func

        # to class instance from parsed arguments
        # is there a better way to do this?
        # log.debug(pargs.__dict__)
        opts = cls(**pargs.__dict__)

        # this validation interface is a bit odd
        cls.validate(opts)
        exit_code = runner_func(opts)
    except Exception as e:
        exit_code = exception_handler(e)

    dt = now() - started_at
    epilogue_handler(exit_code, dt.total_seconds())
    return exit_code


def _runner_with_args(
    args,
    cls,
    runner_func,
    description=None,
    version=None,
    exception_handler=default_exception_handler,
    epilogue_handler=default_epilogue_handler,
) -> int:

    # errors at the argparse level aren't always
    # communicated in an obvious way at this level
    parser = pydantic_class_to_parser(cls, description=description,
                                      version=version)

    # this is a bit of hackery
    parser.set_defaults(func=runner_func, cls=cls)

    return _runner(args, parser, exception_handler, epilogue_handler)


def to_runner(
    cls,
    runner_func,
    description=None,
    version=None,
    exception_handler=default_exception_handler,
    epilogue_handler=default_epilogue_handler,
):
    def f(args):
        return _runner_with_args(
            args,
            cls,
            runner_func,
            description=description,
            version=version,
            exception_handler=exception_handler,
            epilogue_handler=epilogue_handler,
        )

    return f


def run_and_exit(
    cls,
    runner_func,
    description=None,
    version=None,
    exception_handler=default_exception_handler,
    epilogue_handler=default_epilogue_handler,
    args=sys.argv[1:],
):
    sys.exit(
        to_runner(
            cls,
            runner_func,
            description=description,
            version=version,
            exception_handler=exception_handler,
            epilogue_handler=epilogue_handler,
        )(args)
    )


def to_subparser(models: T.Dict[T.AnyStr, SubParser], description=None, version=None) -> ArgumentParser:
    p = ArgumentParser(description=description, formatter_class=ArgumentDefaultsHelpFormatter)

    sp = p.add_subparsers(help='commands')

    for subparser_id, sx in models.items():
        log.debug(("Adding Subparser", subparser_id, sx))

        spx = sp.add_parser(subparser_id, help=sx.description)
        _add_pydantic_class_to_parser(spx, sx.options)
        spx.set_defaults(func=sx.runner_func, cls=sx.options)

    if version is not None:
        _parser_add_version(p, version)

    return p


def to_runner_sp(subparsers: T.Dict[T.AnyStr, T.Type[BaseModel]],
                 description=None, version=None,
                 exception_handler=default_exception_handler,
                 epilogue_handler=default_epilogue_handler) -> T.Callable[[T.List[T.AnyStr]], int]:

    def f(args):
        p = to_subparser(subparsers, description=description, version=version)

        return _runner(args, p, exception_handler, epilogue_handler)

    return f


def run_sp_and_exit(subparsers: T.Dict[T.AnyStr, T.Type[BaseModel]],
                    description: T.Optional[T.AnyStr] = None,
                    version: T.Optional[T.AnyStr] = None,
                    exception_handler=default_exception_handler,
                    epilogue_handler=default_epilogue_handler,
                    args=sys.argv[1:]):

    f = to_runner_sp(subparsers, description=description, version=version,
                     exception_handler=exception_handler,
                     epilogue_handler=epilogue_handler)

    sys.exit(f(args))
