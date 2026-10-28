"""Parser and codegen unit tests."""

from __future__ import annotations

import pytest

from malt import ast_nodes as ast
from malt.errors import ParseError, SemanticError
from malt.parser import parse


def test_precedence():
    stmts = parse("a = 2 + 3 * 4;")
    value = stmts[0].value
    assert isinstance(value, ast.BinaryOperation)
    assert value.op == "+"
    assert isinstance(value.right, ast.BinaryOperation)
    assert value.right.op == "*"


def test_power_right_associative():
    stmts = parse("a = 2^3^2;")
    value = stmts[0].value
    assert value.op == "^"
    assert value.right.op == "^"


def test_colon_lower_precedence_than_add():
    # 1+1:5 -> (1+1):5 -> 2:5
    stmts = parse("a = 1+1:5;")
    value = stmts[0].value
    assert isinstance(value, ast.ColonExpression)


def test_matrix_literal():
    stmts = parse("A = [1 2; 3 4];")
    m = stmts[0].value
    assert isinstance(m, ast.MatrixLiteral)
    assert len(m.rows) == 2
    assert len(m.rows[0]) == 2


def test_multi_output_assignment():
    stmts = parse("[x, y] = f(a, b);")
    a = stmts[0]
    assert isinstance(a, ast.Assignment)
    assert len(a.targets) == 2


def test_if_elseif_else():
    stmts = parse("if a > 0\n x=1;\nelseif a<0\n x=-1;\nelse\n x=0;\nend")
    node = stmts[0]
    assert isinstance(node, ast.IfStatement)
    assert len(node.branches) == 2
    assert node.else_body is not None


def test_function_definition():
    stmts = parse("function [s, p] = calc(a, b)\ns = a + b;\np = a*b;\nend")
    fn = stmts[0]
    assert isinstance(fn, ast.FunctionDefinition)
    assert fn.name == "calc"
    assert fn.outputs == ["s", "p"]
    assert fn.params == ["a", "b"]


def test_anonymous_function():
    stmts = parse("f = @(x) x.^2 + 1;")
    assert isinstance(stmts[0].value, ast.AnonymousFunction)


def test_missing_end():
    with pytest.raises(ParseError):
        parse("if a > 0\n x = 1;")


def test_break_outside_loop():
    from malt.semantic import analyze

    with pytest.raises(SemanticError):
        analyze(parse("break;"))


def test_generate_valid_python():
    from malt.codegen import generate

    src, _ = generate(parse("A = [1 2; 3 4];\nC = A * A;\n"))
    compile(src, "<gen>", "exec")
