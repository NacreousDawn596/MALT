"""Controlled execution environment for compiled MALT units."""

from __future__ import annotations

import builtins as _py_builtins
from typing import Any

from . import runtime as _ml
from .errors import MaltError, ReturnSignal

# A conservative whitelist of Python builtins available to generated code.
# The generated code only references ``_ml`` and plain Python expressions, so
# this is deliberately minimal. It is NOT a security sandbox.
_RESTRICTED_BUILTINS: dict[str, Any] = {
    name: getattr(_py_builtins, name)
    for name in (
        "abs",
        "all",
        "any",
        "bool",
        "complex",
        "dict",
        "enumerate",
        "float",
        "int",
        "isinstance",
        "len",
        "list",
        "max",
        "min",
        "range",
        "repr",
        "round",
        "str",
        "sum",
        "tuple",
        "zip",
        "ZeroDivisionError",
        "ValueError",
        "TypeError",
    )
}


def make_namespace() -> dict[str, Any]:
    """Build a fresh execution namespace."""
    ns: dict[str, Any] = {
        "__builtins__": _RESTRICTED_BUILTINS,
        "_ml": _ml,
    }
    ns.update(_ml.constants())
    return ns


def execute(unit: Any, namespace: dict[str, Any] | None = None) -> dict[str, Any]:
    """Execute a compiled unit in-memory, returning the workspace namespace."""
    if namespace is None:
        namespace = make_namespace()
    _ml.set_current_namespace(namespace)
    try:
        exec(unit.code, namespace)
    except ReturnSignal:
        pass
    except MaltError:
        raise
    finally:
        _ml.set_current_namespace(None)
    return namespace
