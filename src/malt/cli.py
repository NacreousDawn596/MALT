"""Command-line interface for MALT."""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .compiler import compile_source
from .diagnostics import render_error
from .errors import MaltError
from .executor import execute
from .runtime import graphics as _graphics


def _read_source(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def _color_override(args: argparse.Namespace) -> bool | None:
    mode = getattr(args, "color", "auto")
    if mode == "always":
        return True
    if mode == "never":
        return False
    return None


def _render(args: argparse.Namespace, error: BaseException, source: str | None) -> str:
    return render_error(
        error,
        source=source,
        color=_color_override(args),
        style=getattr(args, "diagnostic_format", "text"),
    )


def _add_diagnostic_flags(p: argparse.ArgumentParser) -> None:
    p.add_argument("--color", choices=("auto", "always", "never"), default="auto")
    p.add_argument(
        "--no-color",
        dest="color",
        action="store_const",
        const="never",
        help="alias for --color never",
    )
    p.add_argument(
        "--diagnostic-format", choices=("text", "json"), default="text"
    )


def cmd_eval(args: argparse.Namespace) -> int:
    try:
        unit = compile_source(
            args.expression,
            filename="<eval>",
            optimization_level=args.optimization_level,
        )
        if args.show_generated:
            print(unit.show_generated())
            return 0
        execute(unit)
        _graphics.show_if_any()
        return 0
    except MaltError as e:
        print(_render(args, e, args.expression), file=sys.stderr)
        return 1


def cmd_run(args: argparse.Namespace) -> int:
    source = None
    try:
        source = _read_source(args.file)
        unit = compile_source(
            source, filename=args.file, optimization_level=args.optimization_level
        )
        if args.explain:
            print(unit.coverage_report())
        if args.show_generated:
            print(unit.show_generated())
            return 0
        execute(unit)
        _graphics.show_if_any()
        return 0
    except MaltError as e:
        print(_render(args, e, source), file=sys.stderr)
        if args.debug:
            raise
        return 1


def cmd_compile(args: argparse.Namespace) -> int:
    source = None
    try:
        source = _read_source(args.file)
        unit = compile_source(
            source, filename=args.file, optimization_level=args.optimization_level
        )
        if args.explain:
            print(unit.coverage_report(), file=sys.stderr)
        output = unit.show_generated()
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output)
            print(f"wrote generated Python to {args.output}")
        else:
            print(output)
        return 0
    except MaltError as e:
        print(_render(args, e, source), file=sys.stderr)
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
    p_eval.add_argument("--optimization-level", type=int, choices=(0, 1, 2), default=1)
    _add_diagnostic_flags(p_eval)
    p_eval.set_defaults(func=cmd_eval)

    p_run = sub.add_parser("run", help="run a MATLAB script")
    p_run.add_argument("file")
    p_run.add_argument("--show-generated", action="store_true")
    p_run.add_argument("--explain", action="store_true")
    p_run.add_argument("--debug", action="store_true")
    p_run.add_argument("--optimization-level", type=int, choices=(0, 1, 2), default=1)
    _add_diagnostic_flags(p_run)
    p_run.set_defaults(func=cmd_run)

    p_compile = sub.add_parser("compile", help="emit generated Python")
    p_compile.add_argument("file")
    p_compile.add_argument("-o", "--output", default=None)
    p_compile.add_argument("--explain", action="store_true")
    p_compile.add_argument("--debug", action="store_true")
    p_compile.add_argument("--optimization-level", type=int, choices=(0, 1, 2), default=1)
    _add_diagnostic_flags(p_compile)
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
