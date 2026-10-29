"""Semantic analysis pass.

Validates block structure (break/continue/return placement), duplicate
function definitions, and reserved identifiers before code generation. It also
collects non-fatal warnings (e.g. shadowing a builtin or the imaginary unit).
"""

from __future__ import annotations

from . import ast_nodes as ast
from .builtins import BUILTINS
from .errors import Diagnostic, SemanticError


class _Analyzer:
    def __init__(self) -> None:
        self.loop_depth = 0
        self.in_function = False
        self.functions: set[str] = set()
        self.warnings: list[Diagnostic] = []

    def analyze(self, statements: list[ast.Statement]) -> list[Diagnostic]:
        for s in statements:
            if isinstance(s, ast.FunctionDefinition):
                if s.name in self.functions:
                    raise SemanticError(f"duplicate function '{s.name}'", s.location)
                self.functions.add(s.name)
        for s in statements:
            self.stmt(s)
        return self.warnings

    def _warn(
        self,
        code: str,
        message: str,
        location: ast.SourceLocation,
        hint: str | None = None,
    ) -> None:
        self.warnings.append(Diagnostic("warning", code, message, location, hint))

    def _check_assigned_name(self, name: str, location: ast.SourceLocation) -> None:
        if name in BUILTINS:
            self._warn(
                "W1001",
                f"variable '{name}' shadows a builtin function",
                location,
                hint=f"'{name}(…)' still calls the builtin, but a bare '{name}' "
                "now refers to your variable",
            )
        elif name in ("i", "j"):
            self._warn(
                "W1002",
                f"variable '{name}' shadows the imaginary unit",
                location,
                hint="use a different loop variable (e.g. 'ii' or 'jj'), or "
                "write the literal as '1i'/'1j'",
            )

    def _check_targets(self, node: ast.Assignment) -> None:
        for t in node.targets:
            if isinstance(t, ast.Identifier):
                self._check_assigned_name(t.name, t.location)
            elif isinstance(t, ast.FunctionCall):
                self._check_assigned_name(t.name, t.location)

    def stmt(self, node: ast.Statement) -> None:
        if isinstance(node, ast.BreakStatement):
            if self.loop_depth == 0:
                raise SemanticError("'break' outside of a loop", node.location)
        elif isinstance(node, ast.ContinueStatement):
            if self.loop_depth == 0:
                raise SemanticError("'continue' outside of a loop", node.location)
        elif isinstance(node, ast.ForStatement):
            self._check_assigned_name(node.var, node.location)
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
            self._check_targets(node)
        # Nothing else needs validation at this stage.


def analyze(statements: list[ast.Statement]) -> list[Diagnostic]:
    """Validate and return the list of collected non-fatal warnings."""
    return _Analyzer().analyze(statements)
