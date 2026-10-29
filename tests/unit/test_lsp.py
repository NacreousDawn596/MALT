"""Language server (LSP): framing, diagnostics, hover, completion."""

from __future__ import annotations

import io

from malt.lsp import (
    LspServer,
    completion_items,
    diagnostics_for,
    hover_response,
    read_message,
    write_message,
)


def test_message_framing_roundtrip():
    buf = io.BytesIO()
    write_message(buf, {"jsonrpc": "2.0", "id": 1, "result": {"k": "v"}})
    buf.seek(0)
    msg = read_message(buf)
    assert msg is not None
    assert msg["id"] == 1
    assert msg["result"]["k"] == "v"


def test_diagnostics_for_error():
    diags = diagnostics_for("x = [1 2; 3 4", "file:///t.m")
    assert any(d["severity"] == 1 for d in diags)


def test_diagnostics_for_warning():
    diags = diagnostics_for("sin = 5;\n", "file:///t.m")
    assert any(d["code"] == "W1001" for d in diags)
    assert any(d["severity"] == 2 for d in diags)


def test_hover_for_builtin():
    h = hover_response("x = sin(1);", 0, 5)
    assert h is not None
    assert "sine" in h["contents"]["value"]

def test_hover_unknown_returns_none():
    assert hover_response("x = foo(1);", 0, 5) is None


def test_completion_items_include_builtins_and_keywords():
    labels = {i["label"] for i in completion_items()}
    assert "sin" in labels
    assert "for" in labels
    assert "pi" in labels


def test_server_publishes_diagnostics_on_open():
    out = io.BytesIO()
    server = LspServer(None, out)
    server.handle(
        {
            "jsonrpc": "2.0",
            "method": "textDocument/didOpen",
            "params": {"textDocument": {"uri": "file:///t.m", "text": "sin = 5;\n"}},
        }
    )
    out.seek(0)
    msg = read_message(out)
    assert msg is not None
    assert msg["method"] == "textDocument/publishDiagnostics"
    assert any(d["code"] == "W1001" for d in msg["params"]["diagnostics"])


def test_server_hover_response():
    out = io.BytesIO()
    server = LspServer(None, out)
    server.documents["file:///t.m"] = "x = sin(1);"
    server.handle(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "textDocument/hover",
            "params": {
                "textDocument": {"uri": "file:///t.m"},
                "position": {"line": 0, "character": 5},
            },
        }
    )
    out.seek(0)
    resp = read_message(out)
    assert resp is not None
    assert resp["id"] == 1
    assert "sine" in resp["result"]["contents"]["value"]
