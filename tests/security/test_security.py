"""Security tests: the runtime is not a sandbox, and the language surface
must not expose arbitrary Python evaluation or imports."""

from __future__ import annotations

import pytest

from malt.compiler import compile_source
from malt.errors import MaltError, SemanticError
from malt.executor import execute, make_namespace


def test_no_builtin_import_in_namespace():
    ns = make_namespace()
    assert "__import__" not in ns["__builtins__"]
    assert "open" not in ns["__builtins__"]
    assert "eval" not in ns["__builtins__"]
    assert "exec" not in ns["__builtins__"]


def test_unknown_function_raises():
    # Calling a name that is neither a builtin nor user function is an index
    # attempt on an undefined variable -> runtime error, not arbitrary exec.
    unit = compile_source("open('/etc/passwd');", "s.m")
    with pytest.raises(MaltError):
        execute(unit)


def test_python_keyword_identifier_rejected():
    with pytest.raises(SemanticError):
        compile_source("lambda = 5;", "s.m")


def test_undefined_variable_raises():
    unit = compile_source("disp(secret);", "s.m")
    with pytest.raises(MaltError):
        execute(unit)


def test_generated_code_contains_no_imports():
    # Generated code must not import arbitrary modules.
    unit = compile_source("A = [1 2; 3 4];\nB = A * A;\n", "s.m")
    assert "import " not in unit.generated_source
    assert "__import__" not in unit.generated_source


def test_syntax_error_does_not_crash():
    # Malformed input must produce a controlled diagnostic, not a crash.
    with pytest.raises(MaltError):
        compile_source("if x > 0", "s.m")


def test_matrix_dimension_mismatch_raises_cleanly():
    unit = compile_source("A = [1 2 3];\nB = [1 2];\nC = A + B;\n", "s.m")
    with pytest.raises(MaltError):
        execute(unit)
