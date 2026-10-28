"""The compilation pipeline: lex -> parse -> semantic -> codegen -> compile."""

from __future__ import annotations

from . import codegen, semantic
from .ir import CompilationUnit
from .parser import parse


def compile_source(source: str, filename: str = "<malt>") -> CompilationUnit:
    """Compile MATLAB source into an in-memory CPython code object."""
    statements = parse(source, filename)
    semantic.analyze(statements)
    generated, source_map = codegen.generate(statements, filename)
    code = compile(
        generated,
        filename=f"<malt-generated:{filename}>",
        mode="exec",
    )
    return CompilationUnit(
        filename=filename,
        source=source,
        statements=statements,
        generated_source=generated,
        code=code,
        source_map=source_map,
    )
