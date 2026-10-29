"""Persistent MATLAB-style REPL session.

Features: readline history (persisted to ``~/.malt_history``), tab-completion
of builtins and workspace variables, multi-line block input (``if``/``for``/
``while``/``switch``/``try``/``function`` … ``end``), and ``who``/``whos``/
``clear``/``help`` commands.
"""

from __future__ import annotations

import atexit
import os
import sys
from typing import Any

import numpy as np

from .. import __version__
from ..builtins import BUILTINS
from ..compiler import compile_source
from ..diagnostics import render_error
from ..errors import MaltError
from ..executor import execute, make_namespace
from ..lexer import Lexer
from ..runtime.arrays import as_array
from ..tokens import TokenType

_BANNER = (
    f"MALT {__version__} — MATLAB-compatible runtime\n"
    "Type help for commands or exit to quit.\n"
)

_HISTORY_FILE = os.path.expanduser("~/.malt_history")

_BLOCK_OPENERS = {"if", "for", "while", "switch", "try", "function", "parfor"}


def _is_incomplete(source: str) -> bool:
    """Return True if ``source`` looks like an unterminated block/expression."""
    try:
        tokens = Lexer(source, "<repl>").tokenize()
    except MaltError:
        return False

    bracket_depth = 0
    blocks: list[str] = []
    for tok in tokens:
        t = tok.type
        if t in (TokenType.LPAREN, TokenType.LBRACKET, TokenType.LBRACE):
            bracket_depth += 1
        elif t in (TokenType.RPAREN, TokenType.RBRACKET, TokenType.RBRACE):
            bracket_depth = max(0, bracket_depth - 1)
        elif t == TokenType.IDENT and tok.value in _BLOCK_OPENERS:
            blocks.append(str(tok.value))
        elif t == TokenType.IDENT and tok.value == "end" and bracket_depth == 0:
            if blocks:
                blocks.pop()

    if bracket_depth > 0 or blocks:
        return True
    return source.rstrip().endswith("...")


class Repl:
    def __init__(self) -> None:
        self.namespace: dict[str, Any] = make_namespace()
        self.readline: Any = None
        self._setup_readline()

    # -- readline -----------------------------------------------------------
    def _setup_readline(self) -> None:
        try:
            import readline  # type: ignore[import-not-found]

            self.readline = readline
        except ImportError:
            self.readline = None
            return

        readline.set_history_length(1000)
        try:
            readline.read_history_file(_HISTORY_FILE)
        except (FileNotFoundError, OSError):
            pass
        atexit.register(self._save_history)

        completions: set[str] = set(BUILTINS)

        def completer(text: str, state: int) -> str | None:
            options = sorted(completions | set(self.namespace))
            matches = [o for o in options if o.startswith(text)]
            return matches[state] if state < len(matches) else None

        readline.set_completer(completer)
        readline.parse_and_bind("tab: complete")

    def _save_history(self) -> None:
        if self.readline is None:
            return
        try:
            self.readline.write_history_file(_HISTORY_FILE)
        except OSError:
            pass

    # -- main loop ----------------------------------------------------------
    def run(self) -> int:
        print(_BANNER.rstrip("\n"))
        buffer = ""
        prompt = ">> "
        while True:
            try:
                line = input(prompt)
            except EOFError:
                print()
                return 0
            except KeyboardInterrupt:
                print()
                buffer = ""
                prompt = ">> "
                continue

            if buffer:
                buffer += "\n" + line
            else:
                buffer = line

            if _is_incomplete(buffer):
                prompt = ".. "
                continue

            action = self._handle(buffer)
            buffer = ""
            prompt = ">> "
            if action == "quit":
                return 0

    # -- command handling ---------------------------------------------------
    def _handle(self, source: str) -> str | None:
        stripped = source.strip()
        if not stripped:
            return None
        if stripped in ("exit", "quit"):
            return "quit"
        if stripped in ("help", "?"):
            self._help()
            return None
        if stripped == "who":
            self._who()
            return None
        if stripped == "whos":
            self._whos()
            return None
        if stripped == "clear":
            self.namespace = make_namespace()
            return None
        try:
            unit = compile_source(source, filename="<repl>")
            execute(unit, self.namespace)
        except MaltError as e:
            print(render_error(e, source=source), file=sys.stderr)
        return None

    def _who(self) -> None:
        names = sorted(n for n in self.namespace if not n.startswith("_"))
        if not names:
            return
        for n in names:
            print(n)

    def _whos(self) -> None:
        rows: list[tuple[str, str, str]] = []
        for name in sorted(self.namespace):
            if name.startswith("_"):
                continue
            val = self.namespace[name]
            a = as_array(val)
            if isinstance(a, str):
                cls, shape = "char", f"1x{len(a)}"
            elif isinstance(a, np.ndarray):
                cls = "double" if a.dtype.kind in "fc" else str(a.dtype)
                shape = "x".join(str(s) for s in a.shape)
            else:
                cls = type(a).__name__
                shape = "1x1"
            rows.append((name, shape, cls))

        if not rows:
            return
        w_name = max(len(r[0]) for r in rows)
        w_shape = max(len(r[1]) for r in rows)
        for name, shape, cls in rows:
            print(f"{name:<{w_name}}  {shape:<{w_shape}}  {cls}")

    @staticmethod
    def _help() -> None:
        print("MALT REPL commands:")
        print("  <expr>            evaluate a MATLAB expression")
        print("  who               list workspace variables")
        print("  whos              list variables with size and class")
        print("  clear             clear the workspace")
        print("  help              show this help")
        print("  exit, quit        leave the REPL")
        print("Multi-line blocks (if/for/while/switch/try/function) are entered")
        print("until the matching 'end'.")


def run_repl() -> int:
    return Repl().run()
