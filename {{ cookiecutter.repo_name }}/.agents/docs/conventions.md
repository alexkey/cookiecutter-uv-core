# Code conventions

Read this before writing or reviewing Python code. These conventions describe the
existing code. Match the surrounding module when it is more specific. The analysis
tools enforce part of them: Ruff, ty, Mypy, and Pylint all run under `make lint`.

## Rules

1. Write code for the interpreter pinned in `.python-version`. The code base uses
   syntax that older interpreters reject: type parameter lists such as
   `def configure[**P, R](...)`, `type` aliases, `except A, B:` without parentheses,
   and `lazy` imports. Do not rewrite these for older interpreters.
2. Annotate every function signature. The code must pass both type checkers, ty and
   Mypy.
3. Format with `make format`, which sorts imports and applies the Ruff formatter. Do
   not format by hand against it.
4. Suppress a finding on the line that causes it and for the specific code only. Name
   every tool that reports it: `# noqa: <code>` for Ruff,
   `# pylint: disable=<name>` for Pylint, and
   `# type: ignore[<mypy-code>, ty:<ty-rule>]` for both type checkers in one comment.
5. Use absolute imports from `{{ cookiecutter.repo_name }}`, not relative imports.

## Module structure

- Most modules start with `from __future__ import annotations` and keep imports that
  only annotations need under `if TYPE_CHECKING:`. Types that Pydantic resolves at
  runtime stay regular imports, such as the field types in `app/core/config.py`.
- Modules on the CLI's startup path import with `lazy` the names that only function
  bodies use. Rule 2 of `architecture.md` lists those modules and the exceptions.
- Modules declare their public names in `__all__`.
- A leading underscore marks a private name or a private module, such as
  `_decorators.py`. Tests may import private names of the module under test.
- Names that most callers need are re-exported from the package root,
  `src/{{ cookiecutter.repo_name }}/__init__.py`.
- Module-level constants are `UPPER_CASE`.

## Functions and errors

- Optional behavior switches are keyword-only arguments after `*`. Two recur across
  the code base: `raise_on_exc` selects between raising and logging an error, and
  `verbose` enables lifecycle logging.
- Application-layer exception classes belong in
  `src/{{ cookiecutter.repo_name }}/app/_exceptions.py`.
- An error message must not include a secret. Raise a new exception with `from None`
  where the original exception could carry one, as `check_database_url()` does.
  `from None` drops the exception chain.
- Ruff and Pylint both report a broad `except Exception`. Suppress both findings on
  the line of a required broad handler, as rule 4 describes.
  `tests/system/conftest.py` holds examples.

## Docstrings and comments

- Docstrings follow the Google style. The one-line summary uses the descriptive third
  person, as in "Returns the cached settings." `Args:`, `Returns:`, `Yields:`, and
  `Raises:` sections follow as needed.
- Pylint does not require docstrings. Write one for public functions and classes whose
  behavior, errors, or side effects are not evident from the signature.
- Comments explain why the code is the way it is: invariants, constraints, and
  tradeoffs. Do not restate what the code does.
- Source notes use the form `TAG: text` or `TAG(author): text`, where TAG is one of
  DEBUG, FIXME, TODO, or XXX. `make show-notes` lists them.

## Formatting and limits

- Ruff formats with double quotes and its default line length, because `ruff.toml`
  sets no other. Pylint reports lines longer than the `max-line-length` in `pylintrc`.
- Pylint's design limits, such as the maximum number of arguments, branches, and
  statements, are set under `[DESIGN]` in `pylintrc`.

## Scripts

Files under `etc/scripts/` and `docker/scripts/` are standalone scripts with inline
dependency metadata, run through `uv run --script`. They do not import the package,
and the package does not import them. `etc/scripts/` is formatted and analyzed by the
same targets as `src/` and `tests/`.
