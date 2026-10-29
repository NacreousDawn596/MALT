"""Controlled execution environment for compiled MALT units."""

from __future__ import annotations

import builtins as _py_builtins
import sys
import traceback
from typing import Any

from . import runtime as _ml
from .errors import MaltError, ReturnSignal, RuntimeError_, SourceLocation, UndefinedVariableError

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
        "Exception",
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


def _locate(unit: Any) -> SourceLocation | None:
    """Map the current traceback's generated-code line back to MATLAB source."""
    tb = sys.exc_info()[2]
    for frame in traceback.extract_tb(tb):
        if frame.filename.startswith("<malt-generated"):
            lineno = frame.lineno
            best: SourceLocation | None = None
            for gen_line, loc in unit.source_map:
                if gen_line <= lineno:
                    best = loc
                else:
                    break
            return best
    return None


def _extract_name(err: NameError) -> str:
    msg = str(err)
    if "'" in msg:
        return msg.split("'")[1]
    return msg


def execute(unit: Any, namespace: dict[str, Any] | None = None) -> dict[str, Any]:
    """Execute a compiled unit in-memory, returning the workspace namespace."""
    if namespace is None:
        namespace = make_namespace()
    _ml.set_current_namespace(namespace)
    _ml.set_optimization_level(getattr(unit, "optimization_level", 1))
    try:
        exec(unit.code, namespace)
    except ReturnSignal:
        pass
    except MaltError as e:
        if e.location is None:
            e.location = _locate(unit)
        raise
    except NameError as e:
        raise UndefinedVariableError(
            f"undefined variable or function '{_extract_name(e)}'", _locate(unit),
            hint="MALT is case-sensitive; check the spelling or define the "
            "variable before using it.",
        ) from e
    except Exception as e:
        raise RuntimeError_(str(e), _locate(unit)) from e
    finally:
        _ml.set_current_namespace(None)
    return namespace
