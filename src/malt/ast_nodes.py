"""AST node definitions for MALT.

Nodes are immutable where practical, and every node carries a source
location so that errors can reference the original ``.m`` file.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .errors import SourceLocation


class Node:
    __slots__ = ("location",)

    def __init__(self, location: SourceLocation) -> None:
        self.location = location


# ---------------------------------------------------------------------------
# Expressions
# ---------------------------------------------------------------------------


@dataclass
class NumberLiteral(Node):
    value: float | complex
    location: SourceLocation


@dataclass
class StringLiteral(Node):
    value: str
    location: SourceLocation


@dataclass
class LogicalLiteral(Node):
    value: bool
    location: SourceLocation


@dataclass
class Identifier(Node):
    name: str
    location: SourceLocation


@dataclass
class EndKeyword(Node):
    location: SourceLocation


@dataclass
class MatrixLiteral(Node):
    rows: list[list[Node]]  # each row is a list of expression nodes
    location: SourceLocation


@dataclass
class CellLiteral(Node):
    rows: list[list[Node]]
    location: SourceLocation


@dataclass
class UnaryOperation(Node):
    op: str
    operand: Node
    location: SourceLocation


@dataclass
class BinaryOperation(Node):
    op: str
    left: Node
    right: Node
    location: SourceLocation


@dataclass
class ColonExpression(Node):
    start: Node
    step: Node | None
    end: Node
    location: SourceLocation


@dataclass
class FunctionCall(Node):
    name: str
    args: list[Node]
    location: SourceLocation


@dataclass
class IndexExpression(Node):
    base: Node
    indices: list[Node]  # Node or None (for ':')
    location: SourceLocation


@dataclass
class AnonymousFunction(Node):
    params: list[str]
    body: Node
    location: SourceLocation


@dataclass
class FunctionHandle(Node):
    """A function handle: either a named function or an anonymous function."""

    target: str | AnonymousFunction
    location: SourceLocation


# ---------------------------------------------------------------------------
# Statements
# ---------------------------------------------------------------------------


class Statement(Node):
    suppress: bool = False


@dataclass
class Assignment(Statement):
    targets: list[Node]  # Identifier or IndexExpression
    value: Node
    op: str = "="  # '=', '+=', '-=', '*=', '.*=', '/=', './=', '\\=', '.\\=', '^=', '.^='
    location: SourceLocation = field(default_factory=lambda: SourceLocation("", 0, 0))


@dataclass
class ExpressionStatement(Statement):
    expr: Node
    location: SourceLocation


@dataclass
class IfStatement(Statement):
    branches: list[tuple[Node, list[Statement]]]  # (condition, body)
    else_body: list[Statement] | None
    location: SourceLocation


@dataclass
class ForStatement(Statement):
    var: str
    iterable: Node
    body: list[Statement]
    location: SourceLocation


@dataclass
class WhileStatement(Statement):
    condition: Node
    body: list[Statement]
    location: SourceLocation


@dataclass
class BreakStatement(Statement):
    location: SourceLocation


@dataclass
class ContinueStatement(Statement):
    location: SourceLocation


@dataclass
class ReturnStatement(Statement):
    location: SourceLocation


@dataclass
class FunctionDefinition(Statement):
    name: str
    outputs: list[str]
    params: list[str]
    body: list[Statement]
    location: SourceLocation


# A colon used as a bare index argument, e.g. ``A(:, 2)``.
@dataclass
class ColonArgument(Node):
    location: SourceLocation


__all__ = [
    "Node",
    "NumberLiteral",
    "StringLiteral",
    "LogicalLiteral",
    "Identifier",
    "EndKeyword",
    "MatrixLiteral",
    "CellLiteral",
    "UnaryOperation",
    "BinaryOperation",
    "ColonExpression",
    "FunctionCall",
    "IndexExpression",
    "AnonymousFunction",
    "FunctionHandle",
    "Statement",
    "Assignment",
    "ExpressionStatement",
    "IfStatement",
    "ForStatement",
    "WhileStatement",
    "BreakStatement",
    "ContinueStatement",
    "ReturnStatement",
    "FunctionDefinition",
    "ColonArgument",
]
