"""Function handles (``@name`` and anonymous functions)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


class FunctionHandle:
    """A MATLAB function handle: a callable that remembers its name.

    ``@sin`` yields a ``FunctionHandle`` so that ``func2str`` can recover the
    original name while ``feval``/direct call dispatch through ``__call__``.
    """

    __slots__ = ("name", "fn")

    def __init__(self, name: str, fn: Callable[..., Any]) -> None:
        self.name = name
        self.fn = fn

    def __call__(self, *args: Any) -> Any:
        return self.fn(*args)

    def __repr__(self) -> str:
        return f"@{self.name}"
