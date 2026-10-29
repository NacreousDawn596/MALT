"""Command-line interface for MALT."""

from __future__ import annotations

import argparse
import sys
from typing import Any

from . import __version__
from .compiler import compile_source
from .diagnostics import render_error, render_warning, render_warnings_json
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
    p.add_argument("--no-warnings", action="store_true")
    p.add_argument("--werror", action="store_true", help="treat warnings as errors")


def _emit_warnings(args: argparse.Namespace, unit: Any) -> bool:
    """Print compilation warnings; return True if ``--werror`` should fail."""
    warnings = getattr(unit, "warnings", [])
    if not warnings or getattr(args, "no_warnings", False):
        return False
    style = getattr(args, "diagnostic_format", "text")
    if style == "json":
        print(render_warnings_json(warnings), file=sys.stderr)
    else:
        color = _color_override(args)
        for w in warnings:
            print(render_warning(w, source=unit.source, color=color), file=sys.stderr)
    return bool(getattr(args, "werror", False))


def cmd_eval(args: argparse.Namespace) -> int:
    try:
        unit = compile_source(
            args.expression,
            filename="<eval>",
            optimization_level=args.optimization_level,
        )
        if _emit_warnings(args, unit):
            return 1
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
        if _emit_warnings(args, unit):
            return 1
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
        if _emit_warnings(args, unit):
            return 1
        if args.explain:
            print(unit.coverage_report(), file=sys.stderr)
        output = unit.show_generated()
        if args.source_map:
            with open(args.source_map, "w", encoding="utf-8") as f:
                f.write(unit.source_map_json())
            output += f"\n# sourceMappingURL={args.source_map}\n"
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


def cmd_debug(args: argparse.Namespace) -> int:
    from .debugger import Debugger

    source = _read_source(args.file)
    unit = compile_source(
        source, filename=args.file, optimization_level=args.optimization_level
    )
    if _emit_warnings(args, unit):
        return 1
    dbg = Debugger(unit)
    for line in args.break_lines:
        dbg.breakpoints.add(line)
    dbg.run()
    return 0


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
    p_compile.add_argument("--source-map", default=None, metavar="PATH",
                           help="write a V3 source map to PATH")
    p_compile.add_argument("--explain", action="store_true")
    p_compile.add_argument("--debug", action="store_true")
    p_compile.add_argument("--optimization-level", type=int, choices=(0, 1, 2), default=1)
    _add_diagnostic_flags(p_compile)
    p_compile.set_defaults(func=cmd_compile)

    sub.add_parser("repl", help="start an interactive session").set_defaults(
        func=cmd_repl
    )

    p_debug = sub.add_parser("debug", help="run under the source-level debugger")
    p_debug.add_argument("file")
    p_debug.add_argument(
        "-b",
        "--break",
        dest="break_lines",
        type=int,
        action="append",
        default=[],
        metavar="LINE",
        help="set a breakpoint at LINE",
    )
    p_debug.add_argument("--optimization-level", type=int, choices=(0, 1, 2), default=1)
    _add_diagnostic_flags(p_debug)
    p_debug.set_defaults(func=cmd_debug)

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
