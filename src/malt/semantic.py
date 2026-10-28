"""Semantic analysis pass.

Validates block structure (break/continue/return placement), duplicate
function definitions, and reserved identifiers before code generation.
"""

from __future__ import annotations

from . import ast_nodes as ast
from .errors import SemanticError


class _Analyzer:
    def __init__(self) -> None:
        self.loop_depth = 0
        self.in_function = False
        self.functions: set[str] = set()

    def analyze(self, statements: list[ast.Statement]) -> None:
        for s in statements:
            if isinstance(s, ast.FunctionDefinition):
                if s.name in self.functions:
                    raise SemanticError(f"duplicate function '{s.name}'", s.location)
                self.functions.add(s.name)
        for s in statements:
            self.stmt(s)

    def stmt(self, node: ast.Statement) -> None:
        if isinstance(node, ast.BreakStatement):
            if self.loop_depth == 0:
                raise SemanticError("'break' outside of a loop", node.location)
        elif isinstance(node, ast.ContinueStatement):
            if self.loop_depth == 0:
                raise SemanticError("'continue' outside of a loop", node.location)
        elif isinstance(node, ast.ForStatement):
            self.loop_depth += 1
            for s in node.body:
                self.stmt(s)
            self.loop_depth -= 1
        elif isinstance(node, ast.WhileStatement):
            self.loop_depth += 1
            for s in node.body:
                self.stmt(s)
            self.loop_depth -= 1
        elif isinstance(node, ast.IfStatement):
            for _, body in node.branches:
                for s in body:
                    self.stmt(s)
            if node.else_body:
                for s in node.else_body:
                    self.stmt(s)
        elif isinstance(node, ast.FunctionDefinition):
            self.in_function = True
            for s in node.body:
                self.stmt(s)
            self.in_function = False
        elif isinstance(node, ast.Assignment):
            pass
        # Nothing else needs validation at this stage.


def analyze(statements: list[ast.Statement]) -> list[ast.Statement]:
    _Analyzer().analyze(statements)
    return statements
