from __future__ import annotations

from collections.abc import Callable

import pytest


class FakeTransaction:
    def __init__(self) -> None:
        self.entered = False
        self.exited = False
        self.exit_exc_type: type[BaseException] | None = None

    async def __aenter__(self) -> FakeTransaction:
        self.entered = True
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        _exc: BaseException | None,
        _traceback: object,
    ) -> bool:
        self.exited = True
        self.exit_exc_type = exc_type
        return False


class FakeSession:
    def __init__(self) -> None:
        self.transaction = FakeTransaction()
        self.begin_called = False
        self.closed = False

    def begin(self) -> FakeTransaction:
        self.begin_called = True
        return self.transaction

    async def __aenter__(self) -> FakeSession:
        return self

    async def __aexit__(
        self,
        _exc_type: object,
        _exc: object,
        _traceback: object,
    ) -> bool:
        self.closed = True
        return False


class FakeSessionMaker:
    def __init__(self) -> None:
        self.session = FakeSession()

    def __call__(self) -> FakeSession:
        return self.session


@pytest.fixture
def make_fake_sessionmaker() -> Callable[[], FakeSessionMaker]:
    return FakeSessionMaker
