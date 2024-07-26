# CHANGELOG

## Version 7.0.0

- Drop support for python > 3.10
- CI fixes for explicitly testing for 3.10, 3.11, 3.12

## Version 6.0.0

- Backwards incompatible change. Use `Cmd` model.
- Remove "*sp*" specific functions. No longer necessary because of Cmd interface.
- To migrate forward, inherit from `Cmd` and put your "main" function as `Cmd.run` method.
- `Cmd.run()` should return None (on success) or raise an exception on error.

## Version 5.0.0 (Pydantic 2 support)

(Not published)

- Support for Pydantic >= 2.8
- Pydantic 2 has a different "optional" definition
- Use `CliConfig` instead of `DefaultConfig`
- Many backward incompatible changes to how `bool` are used. Use Pydantic bool casting (e.g., `--dry-run y`, or `--dry-run true`). 
- There's `mypy` related issues with `Field( ......, cli=('-x', '--filter'))`. I don't think pydantic should remove the current `extra` functionality. 


## Version 4.3.0

- Leverage Pydantic validation for enum choices, enabling more complex use-cases

## Version 4.0.0

- Backward incompatible change for semantics of boolean options
- `Field` should be used instead of Config.CLI_EXTRA_OPTIONS

## Version 3.4.0

- Improve support for simple `Enum`s. 

## Version 3.3.0

- Add support for `List` and `Set` fields by [Marius van Niekerk](https://github.com/mariusvniekerk)

## Version 3.2.0

- Add support for emitting autocomplete in bash/zsh using shtab

## Version 3.1.0

- Enable setting the default JSON config file via `PCLI_JSON_CONFIG` env var

## Version 3.0.0

- backwards in compatible changes with default behavior (e.g., generated flags) of boolean options and custom configuration of boolean options.

## Version 2.3.0

- Internals now leverage `mypy` and can catch more Type related errors
