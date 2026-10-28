"""Persistent MATLAB-style REPL session."""

from __future__ import annotations

import sys

from .. import __version__
from ..compiler import compile_source
from ..diagnostics import render_error
from ..errors import MaltError
from ..executor import execute, make_namespace

_BANNER = (
    f"MALT {__version__} — MATLAB-compatible runtime\n"
    "Type help for commands or exit to quit.\n"
)


def run_repl() -> int:
    namespace = make_namespace()
    print(_BANNER.rstrip("\n"))
    while True:
        try:
            line = input(">> ")
        except EOFError:
            print()
            return 0
        except KeyboardInterrupt:
            print()
            continue

        stripped = line.strip()
        if not stripped:
            continue
        if stripped in ("exit", "quit"):
            return 0
        if stripped == "help":
            print("Commands: clear, clc, who, whos, help, exit, quit")
            continue
        if stripped == "who":
            for name in sorted(namespace.keys()):
                if not name.startswith("_"):
                    print(name)
            continue

        try:
            unit = compile_source(line, filename="<repl>")
            execute(unit, namespace)
        except MaltError as e:
            print(render_error(e, source=line), file=sys.stderr)

    return 0
