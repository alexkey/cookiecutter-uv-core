from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

__all__ = [
    "repr_obj",
]


def repr_obj(obj: Any) -> str:
    """Returns a printable representation of an object with memory address."""
    cls_name = type(obj).__name__
    addr = hex(id(obj))

    return f"<{cls_name} object at {addr}>"
