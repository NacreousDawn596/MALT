"""Command-line interface for MALT."""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .compiler import compile_source
from .diagnostics import render_error
from .errors import MaltError
from .executor import execute


def _compile_file(path: str):
    with open(path, encoding="utf-8") as f:
        source = f.read()
    return compile_source(source, filename=path)


def cmd_eval(args: argparse.Namespace) -> int:
    try:
        unit = compile_source(args.expression, filename="<eval>")
        if args.show_generated:
            print(unit.show_generated())
            return 0
        execute(unit)
        return 0
    except MaltError as e:
        print(render_error(e, source=args.expression), file=sys.stderr)
        return 1


def cmd_run(args: argparse.Namespace) -> int:
    try:
        unit = _compile_file(args.file)
        if args.show_generated:
            print(unit.show_generated())
            return 0
        execute(unit)
        return 0
    except MaltError as e:
        print(render_error(e), file=sys.stderr)
        if args.debug:
            raise
        return 1


def cmd_compile(args: argparse.Namespace) -> int:
    try:
        unit = _compile_file(args.file)
        output = unit.show_generated()
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output)
            print(f"wrote generated Python to {args.output}")
        else:
            print(output)
        return 0
    except MaltError as e:
        print(render_error(e), file=sys.stderr)
        if args.debug:
            raise
        return 1


def cmd_repl(args: argparse.Namespace) -> int:
    from .repl.session import run_repl

    return run_repl()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="malt",
        description="MALT — a MATLAB-compatible language runtime",
    )
    parser.add_argument("--version", action="version", version=f"malt {__version__}")
    sub = parser.add_subparsers(dest="command")

    p_eval = sub.add_parser("eval", help="evaluate a MATLAB expression")
    p_eval.add_argument("expression")
    p_eval.add_argument("--show-generated", action="store_true")
    p_eval.set_defaults(func=cmd_eval)

    p_run = sub.add_parser("run", help="run a MATLAB script")
    p_run.add_argument("file")
    p_run.add_argument("--show-generated", action="store_true")
    p_run.add_argument("--debug", action="store_true")
    p_run.set_defaults(func=cmd_run)

    p_compile = sub.add_parser("compile", help="emit generated Python")
    p_compile.add_argument("file")
    p_compile.add_argument("-o", "--output", default=None)
    p_compile.add_argument("--debug", action="store_true")
    p_compile.set_defaults(func=cmd_compile)

    sub.add_parser("repl", help="start an interactive session").set_defaults(
        func=cmd_repl
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
