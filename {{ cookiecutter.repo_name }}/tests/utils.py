from __future__ import annotations

import io
import json
from typing import Any

type LogRecord = dict[str, Any]


def parse_json_lines(stream: io.StringIO) -> list[LogRecord]:
    records: list[LogRecord] = []

    for line in stream.getvalue().splitlines():
        if not line.strip():
            continue

        obj = json.loads(line)
        assert isinstance(obj, dict), f"expected a JSON object, not {type(obj)!r}"
        records.append(obj)

    return records


def assert_log_event_count(
    stream: io.StringIO, match: str, *, count: int = 1
) -> list[LogRecord]:
    """Asserts how many captured log records contain a substring in their event.

    Args:
        stream: JSON log lines captured by the `cap_json_logs` fixture.
        match: Substring searched for within each record's `event` message.
        count: Exact number of matching records the stream must contain.

    Returns:
        The matching records in capture order, for further inspection by the caller.
    """
    matches = [
        record for record in parse_json_lines(stream) if match in record["event"]
    ]
    assert len(matches) == count, (
        f"expected {count} log event(s) matching {match!r}, found {len(matches)}"
    )
    return matches


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
    if host is None:
        authority = ""
    else:
        authority = f"{host}:{port}" if port is not None else host

    credentials = user if password is None else f"{user}:{password}"
    path = f"/{database}" if database is not None else ""

    return f"{driver}://{credentials}@{authority}{path}{query}"


VALID_DATABASE_URL = _database_url()
