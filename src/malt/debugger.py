"""Source-level debugger for MALT programs.

``malt debug file.m`` runs a script under a Python line tracer that maps
generated lines back to MATLAB source lines (via the source map) and pauses at
breakpoints / step boundaries. The prompt is a small pdb-like REPL operating on
the *MATLAB* source, not the generated Python.
"""

from __future__ import annotations

import sys
from typing import Any

from .compiler import compile_source
from .errors import MaltError, SourceLocation
from .executor import execute, make_namespace


class _Quit(BaseException):
    """Internal signal to unwind the traced execution."""


class Debugger:
    def __init__(self, unit: Any) -> None:
        self.unit = unit
        self.breakpoints: set[int] = set()
        self.step = True  # stop at the first statement
        self._namespace: dict[str, Any] | None = None
        self._last_src_line: int | None = None
        self._in_prompt = False
        self._quitting = False

    # -- source mapping -----------------------------------------------------
    def _map(self, gen_line: int) -> SourceLocation | None:
        best: SourceLocation | None = None
        for g, loc in self.unit.source_map:
            if g <= gen_line:
                best = loc
            else:
                break
        return best

    # -- execution ----------------------------------------------------------
    def run(self, namespace: dict[str, Any] | None = None) -> dict[str, Any]:
        namespace = namespace if namespace is not None else make_namespace()
        self._namespace = namespace
        sys.settrace(self._trace)
        try:
            execute(self.unit, namespace)
        except _Quit:
            pass
        finally:
            sys.settrace(None)
        return namespace

    def _trace(self, frame: Any, event: str, arg: Any) -> Any:
        if self._in_prompt:
            return None
        if event != "line":
            return self._trace
        if not frame.f_code.co_filename.startswith("<malt-generated"):
            return self._trace
        loc = self._map(frame.f_lineno)
        if loc is None:
            return self._trace
        src_line = loc.line
        if src_line == self._last_src_line:
            return self._trace
        self._last_src_line = src_line
        if self.step or src_line in self.breakpoints:
            self.step = False
            self._prompt(frame, src_line)
            if self._quitting:
                raise _Quit()
        return self._trace

    # -- interaction --------------------------------------------------------
    def _prompt(self, frame: Any, src_line: int) -> None:
        self._in_prompt = True
        try:
            self._show_context(src_line)
            while True:
                try:
                    raw = input("(maltdbg) ")
                except EOFError:
                    raw = "q"
                except KeyboardInterrupt:
                    print()
                    continue
                cmd = raw.strip()
                if not cmd:
                    continue
                if cmd in ("q", "quit", "exit"):
                    self._quitting = True
                    return
                if cmd in ("c", "continue"):
                    return
                if cmd in ("n", "next", "s", "step"):
                    self.step = True
                    return
                if cmd in ("l", "list"):
                    self._show_context(src_line, window=20)
                    continue
                if cmd in ("w", "where"):
                    print(f"  at {self.unit.filename}:{src_line}")
                    continue
                if cmd in ("b", "break"):
                    self._list_breakpoints()
                    continue
                if cmd.startswith("b ") or cmd.startswith("break "):
                    self._add_breakpoint(cmd.split(None, 1)[1])
                    continue
                if cmd in ("h", "help", "?"):
                    self._help()
                    continue
                if cmd.startswith("p ") or cmd.startswith("print "):
                    self._print_expr(cmd.split(None, 1)[1])
                    continue
                print(f"unknown command {raw!r} (type 'h' for help)")
        finally:
            self._in_prompt = False

    def _show_context(self, src_line: int, window: int = 6) -> None:
        lines = self.unit.source.splitlines()
        lo = max(1, src_line - window // 2)
        hi = min(len(lines), src_line + window // 2)
        print(f"  {self.unit.filename}:{src_line}")
        for i in range(lo, hi + 1):
            marker = "> " if i == src_line else "  "
            print(f"{marker}{i:>4}  {lines[i - 1]}")

    def _list_breakpoints(self) -> None:
        if not self.breakpoints:
            print("no breakpoints")
            return
        for b in sorted(self.breakpoints):
            print(f"  breakpoint at {self.unit.filename}:{b}")

    def _add_breakpoint(self, spec: str) -> None:
        try:
            line = int(spec.strip())
        except ValueError:
            print("breakpoint requires a line number")
            return
        self.breakpoints.add(line)
        print(f"breakpoint set at {self.unit.filename}:{line}")

    def _print_expr(self, expr: str) -> None:
        try:
            unit = compile_source(expr, "<dbg>")
            execute(unit, self._namespace)
        except MaltError as e:
            print(f"error: {e.message}")
        except Exception as e:  # noqa: BLE001 - debugger evaluates arbitrary input
            print(f"error: {e}")

    @staticmethod
    def _help() -> None:
        print(
            "commands:\n"
            "  c, continue   run to the next breakpoint\n"
            "  n, next, s, step  execute one statement\n"
            "  b, break [N]  list or set a breakpoint at line N\n"
            "  l, list       show source around the current line\n"
            "  w, where      show the current location\n"
            "  p, print EXPR evaluate EXPR in the workspace and print it\n"
            "  h, help       show this help\n"
            "  q, quit       abort execution\n"
        )
