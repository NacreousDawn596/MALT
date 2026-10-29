"""A minimal Language Server Protocol (LSP) server for MALT, over stdio.

Implements just enough of the protocol for a useful editor experience without
any third-party dependencies:

- lifecycle: ``initialize``, ``initialized``, ``shutdown``, ``exit``
- ``textDocument/didOpen`` / ``didChange`` → publish diagnostics (parse/semantic
  errors and warnings) via ``textDocument/publishDiagnostics``
- ``textDocument/hover`` → short help for builtin functions and keywords
- ``textDocument/completion`` → builtin functions, keywords, and constants

Run it with ``malt lsp`` (or ``python -m malt lsp``). It speaks JSON-RPC over
stdin/stdout with ``Content-Length`` framing, so any LSP client (VS Code,
Neovim, Helix, …) can attach to it.
"""

from __future__ import annotations

import json
import sys
from typing import Any

from .builtins import BUILTINS
from .compiler import compile_source
from .errors import Diagnostic, MaltError

# LSP completion-item kinds.
_KIND_FUNCTION = 3
_KIND_KEYWORD = 14
_KIND_VARIABLE = 6
_KIND_CONSTANT = 21

# LSP diagnostic severities.
_SEV_ERROR = 1
_SEV_WARNING = 2

_KEYWORDS = (
    "if", "elseif", "else", "for", "while", "end", "break", "continue",
    "return", "function", "switch", "case", "otherwise", "try", "catch",
    "global", "parfor",
)

_CONSTANTS = ("pi", "eps", "Inf", "NaN", "true", "false", "i", "j")

# Brief documentation for the most common builtins; others fall back to a
# generic one-liner.
_BUILTIN_DOCS: dict[str, str] = {
    "zeros": "`zeros(m, n)` — an m-by-n matrix of zeros.",
    "ones": "`ones(m, n)` — an m-by-n matrix of ones.",
    "eye": "`eye(n)` — the n-by-n identity matrix.",
    "size": "`size(A)` — the dimensions of A.",
    "length": "`length(x)` — the largest dimension of x.",
    "numel": "`numel(A)` — the number of elements in A.",
    "reshape": "`reshape(A, m, n)` — reshape A to m-by-n (column-major).",
    "linspace": "`linspace(a, b, n)` — n evenly spaced points from a to b.",
    "sum": "`sum(A)` — sum along the first non-singleton dimension.",
    "mean": "`mean(A)` — mean along the first non-singleton dimension.",
    "max": "`max(A)` — maximum along the first non-singleton dimension.",
    "min": "`min(A)` — minimum along the first non-singleton dimension.",
    "plot": "`plot(x, y)` — a 2-D line plot.",
    "disp": "`disp(x)` — display a value.",
    "fprintf": "`fprintf(fmt, ...)` — formatted output (cycles the format).",
    "sin": "`sin(x)` — sine, element-wise.",
    "cos": "`cos(x)` — cosine, element-wise.",
    "sqrt": "`sqrt(x)` — square root, element-wise.",
    "exp": "`exp(x)` — e^x, element-wise.",
    "abs": "`abs(x)` — absolute value.",
    "integral": "`integral(f, a, b)` — numerical integration.",
    "fzero": "`fzero(f, x0)` — find a root near x0.",
}


# ---------------------------------------------------------------------------
# JSON-RPC framing
# ---------------------------------------------------------------------------


def read_message(stream: Any) -> dict[str, Any] | None:
    headers: dict[str, str] = {}
    while True:
        line = stream.readline()
        if not line:
            return None
        line = line.decode("utf-8") if isinstance(line, bytes) else line
        line = line.rstrip("\r\n")
        if line == "":
            break
        key, _, value = line.partition(":")
        headers[key.strip().lower()] = value.strip()
    length = int(headers.get("content-length", "0"))
    body = stream.read(length)
    if isinstance(body, bytes):
        body = body.decode("utf-8")
    return json.loads(body)


def write_message(stream: Any, payload: dict[str, Any]) -> None:
    data = json.dumps(payload).encode("utf-8")
    stream.write(f"Content-Length: {len(data)}\r\n\r\n".encode())
    stream.write(data)
    stream.flush()


# ---------------------------------------------------------------------------
# Position / diagnostic conversion
# ---------------------------------------------------------------------------


def _range(loc: Any) -> dict[str, dict[str, int]]:
    end_line = getattr(loc, "end_line", None) or loc.line
    end_col = getattr(loc, "end_column", None) or (loc.column + 1)
    return {
        "start": {"line": loc.line - 1, "character": loc.column - 1},
        "end": {"line": end_line - 1, "character": end_col - 1},
    }


def _lsp_diagnostic(diag: Diagnostic | MaltError) -> dict[str, Any]:
    severity = _SEV_WARNING if isinstance(diag, Diagnostic) else _SEV_ERROR
    code: str = diag.code
    message = diag.message
    hint = getattr(diag, "hint", None)
    if hint:
        message = f"{message}\n{hint}"
    d: dict[str, Any] = {
        "range": _range(diag.location),
        "severity": severity,
        "code": code,
        "source": "malt",
        "message": message,
    }
    return d


def diagnostics_for(text: str, uri: str) -> list[dict[str, Any]]:
    """Compile ``text`` and return LSP diagnostics (errors + warnings)."""
    try:
        unit = compile_source(text, filename=uri)
    except MaltError as e:
        return [_lsp_diagnostic(e)]
    result = [_lsp_diagnostic(w) for w in unit.warnings]
    return result


def _word_at(text: str, line: int, char: int) -> str | None:
    lines = text.splitlines()
    if line < 0 or line >= len(lines):
        return None
    content = lines[line]
    if char < 0 or char > len(content):
        return None
    lo = char
    while lo > 0 and (content[lo - 1].isalnum() or content[lo - 1] == "_"):
        lo -= 1
    hi = char
    while hi < len(content) and (content[hi].isalnum() or content[hi] == "_"):
        hi += 1
    word = content[lo:hi]
    return word or None


# ---------------------------------------------------------------------------
# Request handlers (pure, testable)
# ---------------------------------------------------------------------------


def hover_response(text: str, line: int, char: int) -> dict[str, Any] | None:
    word = _word_at(text, line, char)
    if not word:
        return None
    if word in _BUILTIN_DOCS:
        value = _BUILTIN_DOCS[word]
    elif word in BUILTINS:
        value = f"`{word}(...)` — builtin function."
    elif word in _KEYWORDS:
        value = f"`{word}` — control-flow keyword."
    elif word in _CONSTANTS:
        value = f"`{word}` — builtin constant."
    else:
        return None
    return {"contents": {"kind": "markdown", "value": value}}


def completion_items() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for name in sorted(BUILTINS):
        items.append({"label": name, "kind": _KIND_FUNCTION, "detail": "function"})
    for name in _KEYWORDS:
        items.append({"label": name, "kind": _KIND_KEYWORD, "detail": "keyword"})
    for name in _CONSTANTS:
        items.append({"label": name, "kind": _KIND_CONSTANT, "detail": "constant"})
    return items


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------


class LspServer:
    def __init__(self, inp: Any, out: Any) -> None:
        self.inp = inp
        self.out = out
        self.documents: dict[str, str] = {}
        self._shutdown = False

    def _notify(self, method: str, params: dict[str, Any]) -> None:
        write_message(self.out, {"jsonrpc": "2.0", "method": method, "params": params})

    def _respond(self, msg_id: Any, result: Any) -> None:
        write_message(self.out, {"jsonrpc": "2.0", "id": msg_id, "result": result})

    def _publish_diagnostics(self, uri: str) -> None:
        text = self.documents.get(uri, "")
        self._notify(
            "textDocument/publishDiagnostics",
            {"uri": uri, "diagnostics": diagnostics_for(text, uri)},
        )

    def handle(self, msg: dict[str, Any]) -> bool:
        """Handle one message; return False to stop the loop (``exit``)."""
        method = msg.get("method")
        msg_id = msg.get("id")

        if method == "initialize":
            self._respond(
                msg_id,
                {
                    "capabilities": {
                        "textDocumentSync": 1,
                        "hoverProvider": True,
                        "completionProvider": {"triggerCharacters": []},
                    },
                    "serverInfo": {"name": "malt", "version": "0.3.0"},
                },
            )
        elif method == "initialized":
            pass
        elif method == "shutdown":
            self._shutdown = True
            self._respond(msg_id, None)
        elif method == "exit":
            return False
        elif method == "textDocument/didOpen":
            doc = msg["params"]["textDocument"]
            self.documents[doc["uri"]] = doc["text"]
            self._publish_diagnostics(doc["uri"])
        elif method == "textDocument/didChange":
            params = msg["params"]
            uri = params["textDocument"]["uri"]
            text = params["contentChanges"][0]["text"]
            self.documents[uri] = text
            self._publish_diagnostics(uri)
        elif method == "textDocument/didClose":
            self.documents.pop(msg["params"]["textDocument"]["uri"], None)
        elif method == "textDocument/hover":
            params = msg["params"]
            uri = params["textDocument"]["uri"]
            pos = params["position"]
            result = hover_response(self.documents.get(uri, ""), pos["line"], pos["character"])
            self._respond(msg_id, result)
        elif method == "textDocument/completion":
            self._respond(msg_id, {"isIncomplete": False, "items": completion_items()})
        return True

    def run(self) -> int:
        while True:
            msg = read_message(self.inp)
            if msg is None:
                return 0
            if not self.handle(msg):
                return 0


def run() -> int:
    return LspServer(sys.stdin.buffer, sys.stdout.buffer).run()


if __name__ == "__main__":
    raise SystemExit(run())
