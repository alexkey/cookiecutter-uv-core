from __future__ import annotations

from collections.abc import Callable
from typing import TextIO, cast

import pytest


class _FakeStream:
    def __init__(self, *, isatty: bool) -> None:
        self._isatty = isatty

    def isatty(self) -> bool:
        return self._isatty


@pytest.fixture
def make_fake_stream() -> Callable[..., TextIO]:
    def factory(*, isatty: bool) -> TextIO:
        return cast(TextIO, _FakeStream(isatty=isatty))

    return factory
