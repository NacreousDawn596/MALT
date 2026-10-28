"""Compatibility predicates, string helpers, and any/all/num2str."""

from __future__ import annotations

from conftest import run_source, scalar


def test_isnumeric():
    ns, _ = run_source("r1 = isnumeric([1 2]);\nr2 = isnumeric('a');\n")
    assert scalar(ns, "r1") == 1
    assert scalar(ns, "r2") == 0


def test_ischar():
    ns, _ = run_source("r1 = ischar('abc');\nr2 = ischar(3);\n")
    assert scalar(ns, "r1") == 1
    assert scalar(ns, "r2") == 0


def test_isempty():
    ns, _ = run_source("r1 = isempty([]);\nr2 = isempty([1 2]);\nr3 = isempty('');\n")
    assert scalar(ns, "r1") == 1
    assert scalar(ns, "r2") == 0
    assert scalar(ns, "r3") == 1


def test_isscalar():
    ns, _ = run_source("r1 = isscalar(5);\nr2 = isscalar([1 2]);\n")
    assert scalar(ns, "r1") == 1
    assert scalar(ns, "r2") == 0


def test_isvector_ismatrix():
    ns, _ = run_source(
        "r1 = isvector([1 2 3]);\nr2 = isvector([1 2; 3 4]);\nr3 = ismatrix([1 2; 3 4]);\n"
    )
    assert scalar(ns, "r1") == 1
    assert scalar(ns, "r2") == 0
    assert scalar(ns, "r3") == 1


def test_isrow_iscolumn():
    ns, _ = run_source("r1 = isrow([1 2 3]);\nr2 = iscolumn([1 2 3]);\nr3 = iscolumn([1; 2; 3]);\n")
    assert scalar(ns, "r1") == 1
    assert scalar(ns, "r2") == 0
    assert scalar(ns, "r3") == 1


def test_isreal():
    ns, _ = run_source("r1 = isreal([1 2]);\nr2 = isreal([1+2i 3]);\n")
    assert scalar(ns, "r1") == 1
    assert scalar(ns, "r2") == 0


def test_any_all():
    ns, _ = run_source("a = [1 2 3];\nb = any(a > 2);\nc = all(a > 0);\n")
    assert scalar(ns, "b") == 1
    assert scalar(ns, "c") == 1


def test_any_all_matrix_dim():
    ns, _ = run_source("a = [1 0; 0 1];\nb = any(a, 1);\nc = all(a, 2);\n")
    assert scalar(ns, "b") == 1  # each column has a nonzero
    assert scalar(ns, "c") == 0  # no row is all nonzero


def test_lower_upper():
    ns, _ = run_source("a = lower('HeLLo');\nb = upper('world');\n")
    assert ns["a"] == "hello"
    assert ns["b"] == "WORLD"


def test_strcmp_strcmpi():
    ns, _ = run_source(
        "a = strcmp('abc', 'abc');\nb = strcmp('abc', 'abd');\nc = strcmpi('ABC', 'abc');\n"
    )
    assert scalar(ns, "a") == 1
    assert scalar(ns, "b") == 0
    assert scalar(ns, "c") == 1


def test_strcat():
    ns, _ = run_source("s = strcat('foo', 'bar', 'baz');\n")
    assert ns["s"] == "foobarbaz"


def test_num2str_scalar():
    ns, _ = run_source("s = num2str(3.5);\n")
    assert ns["s"] == "3.5"
