"""Qt6 GUI REPL (headless smoke tests using the offscreen platform)."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
if os.environ.get("MALT_QT6_PLUGIN_PATH"):
    os.environ.setdefault(
        "QT_QPA_PLATFORM_PLUGIN_PATH", os.environ["MALT_QT6_PLUGIN_PATH"]
    )

import pytest

pytest.importorskip("PyQt6.QtWidgets")


@pytest.fixture(scope="session")
def qapp():
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    return app


@pytest.fixture()
def window(qapp):
    from malt.gui import MainWindow

    return MainWindow()


def test_gui_evaluates_expressions(qapp, window):
    window.repl._handle("A = [1 2; 3 4];")
    window.repl._handle("x = sum(A);")
    assert window.repl.namespace["A"].tolist() == [[1.0, 2.0], [3.0, 4.0]]
    assert window.repl.namespace["x"].tolist() == [[4.0, 6.0]]


def test_gui_workspace_refresh(qapp, window):
    window.repl._handle("v = 42;")
    window._refresh_workspace()
    names = [
        window._workspace.topLevelItem(i).text(0)
        for i in range(window._workspace.topLevelItemCount())
    ]
    assert "v" in names


def test_gui_clear_resets_workspace(qapp, window):
    window.repl._handle("y = 1;")
    window.repl._handle("clear")
    assert "y" not in window.repl.namespace


def test_gui_submit_multi_line(qapp, window):
    window._input.setText("if 1 > 0")
    window._submit()
    assert window._buffer == "if 1 > 0"
    assert window._prompt.text() == "…"
    window._input.setText("  x = 7;")
    window._submit()
    window._input.setText("end")
    window._submit()
    assert window.repl.namespace["x"] == 7
    assert window._prompt.text() == "»"
