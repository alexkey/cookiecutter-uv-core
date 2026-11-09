from __future__ import annotations

import io
import json
from typing import Any, Never

import pytest

type LogRecord = dict[str, Any]


def fail_without_traceback(reason: str) -> Never:
    """Fails the current test, reporting `reason` with no traceback.

    Also omits the chain of an exception being handled.
    """
    raise pytest.fail.Exception(reason, pytrace=False) from None


# The functions below set the local variable `__tracebackhide__` to `True`, which
# excludes their frames from the Pytest traceback and ends it at the line of the calling
# test.


def parse_json_lines(stream: io.StringIO) -> list[LogRecord]:
    """Parses captured JSON log lines into records, skipping blank lines.

    Raises:
        json.JSONDecodeError: If a line is not valid JSON.
        AssertionError: If a line holds a JSON value other than an object.
    """
    __tracebackhide__ = True  # pylint: disable=unused-variable

    records: list[LogRecord] = []

    for line in stream.getvalue().splitlines():
        if not line.strip():
            continue

        obj = json.loads(line)
        assert isinstance(obj, dict), f"expected a JSON object, not {type(obj)!r}"
        records.append(obj)

    return records


def assert_log_event(
    stream: io.StringIO, match: str, *, count: int = 1, **fields: object
) -> list[LogRecord]:
    """Asserts captured log records match an event substring and expected fields.

    Args:
        stream: JSON log lines captured by the `cap_json_logs` fixture.
        match: Substring searched for within each record's `event` message.
        count: Exact number of matching records the stream must contain.
        **fields: Expected values that every matching record must hold, compared by
            equality (e.g. `level="error"`).

    Returns:
        The matching records in capture order, for further inspection by the caller.

    Raises:
        AssertionError: If the stream does not hold exactly `count` records matching
            `match`, or a matching record's field does not equal its expected value.
    """
    __tracebackhide__ = True  # pylint: disable=unused-variable

    matches = [
        record for record in parse_json_lines(stream) if match in record["event"]
    ]

    assert len(matches) == count, (
        f"expected {count} log event(s) matching {match!r}, found {len(matches)}"
    )

    for record in matches:
        for key, expected in fields.items():
            actual = record.get(key)
            assert actual == expected, (
                f"log event {match!r}: expected {key}={expected!r}, got {actual!r}"
            )

    return matches


def assert_log_exception(
    stream: io.StringIO,
    match: str,
    exc_type: str,
    *,
    exc_value: str | None = None,
    level: str = "error",
) -> LogRecord:
    """Asserts a captured record logged an exception of the expected type.

    Args:
        stream: JSON log lines captured by the `cap_json_logs` fixture.
        match: Substring searched for within the record's `event` message.
        exc_type: Expected exception class name, e.g. "KeyError".
        exc_value: If given, the expected `str(exc)` of the matched exception. For
            `KeyError` this retains the surrounding quotes, e.g. "'missing'".
        level: Expected record `level`. Defaults to "error".

    Returns:
        The matching record, for further inspection such as its traceback frames.

    Raises:
        AssertionError: If no single record matches, the record carries no `exception`,
            or the chain lacks an entry of `exc_type`.
    """
    __tracebackhide__ = True  # pylint: disable=unused-variable

    [record] = assert_log_event(stream, match, count=1, level=level)

    chain = record.get("exception")
    assert isinstance(chain, list) and chain, (
        f"log event {match!r}: expected a logged exception, got {chain!r}"
    )

    types = [entry["exc_type"] for entry in chain]
    assert exc_type in types, (
        f"log event {match!r}: expected exception {exc_type!r} in the chain, "
        f"got {types!r}"
    )

    if exc_value is not None:
        values = [
            entry["exc_value"] for entry in chain if entry["exc_type"] == exc_type
        ]
        assert exc_value in values, (
            f"log event {match!r}: expected exc_value {exc_value!r} for {exc_type!r}, "
            f"got {values!r}"
        )

    return record


_DRIVER = "postgresql+asyncpg"
_USER = "user"
_PASSWORD = "passwd"
_HOST = "host"
_PORT = 5432
_DATABASE = "db"


def _database_url(
    *,
    driver: str = _DRIVER,
    user: str = _USER,
    password: str | None = _PASSWORD,
    host: str | None = _HOST,
    port: int | None = _PORT,
    database: str | None = _DATABASE,
    query: str = "",
) -> str:
    """Builds a database URL from components, omitting each component set to None.

    A None host also omits the port.
    """
    if host is None:
        authority = ""
    else:
        authority = f"{host}:{port}" if port is not None else host

    credentials = user if password is None else f"{user}:{password}"
    path = f"/{database}" if database is not None else ""

    return f"{driver}://{credentials}@{authority}{path}{query}"


VALID_DATABASE_URL = _database_url()

MALFORMED_PORT_DATABASE_URLS = (
    f"{_DRIVER}://{_USER}:{_PASSWORD}/{_DATABASE}",  # <- `@` separator omitted
    _database_url(password=f"p@ss:{_PASSWORD}"),     # <- unescaped `@` and `:` in the password
)
