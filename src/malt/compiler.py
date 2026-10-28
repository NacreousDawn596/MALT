"""The compilation pipeline: lex -> parse -> semantic -> codegen -> compile."""

from __future__ import annotations

from functools import lru_cache

from . import codegen, semantic
from .ir import CompilationUnit
from .parser import parse


@lru_cache(maxsize=128)
def _compile_cached(source: str, filename: str, optimization_level: int) -> CompilationUnit:
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
        optimization_level=optimization_level,
    )


def compile_source(
    source: str, filename: str = "<malt>", optimization_level: int = 1
) -> CompilationUnit:
    """Compile MATLAB source into an in-memory CPython code object.

    Results are cached by ``(source, filename, optimization_level)``. The cache
    holds only immutable compilation artifacts (AST, generated source, code
    object, source map) — never execution results or workspaces.
    """
    return _compile_cached(source, filename, optimization_level)


def cache_info():
    """Return (hits, misses, maxsize, currsize) for the compilation cache."""
    return _compile_cached.cache_info()


def cache_clear() -> None:
    """Clear the compilation cache."""
    _compile_cached.cache_clear()
