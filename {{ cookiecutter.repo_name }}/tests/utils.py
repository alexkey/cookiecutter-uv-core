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
