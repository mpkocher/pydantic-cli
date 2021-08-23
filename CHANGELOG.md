# CHANGELOG

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