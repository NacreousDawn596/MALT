"""Qt6 notebook-style GUI REPL (headless smoke tests, offscreen platform)."""

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


def test_gui_evaluates_cell(qapp, window):
    cell = window.cells[0]
    cell.input.setPlainText("A = [1 2; 3 4];")
    window._execute(cell, move_next=False)
    assert window.repl.namespace["A"].tolist() == [[1.0, 2.0], [3.0, 4.0]]


def test_gui_edit_previous_cell(qapp, window):
    cell = window.cells[0]
    cell.input.setPlainText("x = 1")
    window._execute(cell, move_next=False)
    assert window.repl.namespace["x"] == 1
    assert "1" in cell.output.toPlainText()
    # Edit and re-run the same cell; output is replaced, not appended.
    cell.input.setPlainText("x = 2")
    window._execute(cell, move_next=False)
    assert window.repl.namespace["x"] == 2
    assert "2" in cell.output.toPlainText()
    assert "1" not in cell.output.toPlainText()


def test_gui_shared_workspace_across_cells(qapp, window):
    c0 = window.cells[0]
    c0.input.setPlainText("x = 5;")
    window._execute(c0, move_next=False)
    c1 = window._add_cell()
    c1.input.setPlainText("y = x + 1")
    window._execute(c1, move_next=False)
    assert float(window.repl.namespace["y"]) == 6.0


def test_gui_workspace_refresh(qapp, window):
    window.cells[0].input.setPlainText("v = 42;")
    window._execute(window.cells[0], move_next=False)
    window._refresh_workspace()
    names = [
        window._workspace.topLevelItem(i).text(0)
        for i in range(window._workspace.topLevelItemCount())
    ]
    assert "v" in names


def test_gui_clear_resets_workspace(qapp, window):
    window.cells[0].input.setPlainText("y = 1;")
    window._execute(window.cells[0], move_next=False)
    window.repl._handle("clear")
    assert "y" not in window.repl.namespace


def test_gui_run_and_next_adds_cell(qapp, window):
    window.cells[0].input.setPlainText("z = 1;")
    window._run_cell_and_next(window.cells[0])
    assert len(window.cells) == 2  # a new empty cell was added


def test_gui_run_all_resets_and_runs_everything(qapp, window):
    window.cells[0].input.setPlainText("a = 1;")
    c1 = window._add_cell()
    c1.input.setPlainText("b = a + 1;")
    c2 = window._add_cell()
    c2.input.setPlainText("c = b * 2;")
    window._run_all()
    assert window.repl.namespace["a"] == 1
    assert float(window.repl.namespace["c"]) == 4.0


def test_gui_delete_cell(qapp, window):
    window.cells[0].input.setPlainText("x = 1;")
    c1 = window._add_cell()
    c1.input.setPlainText("y = 2;")
    window._delete_cell(c1)
    assert len(window.cells) == 1
    assert window.cells[0].text().strip() == "x = 1;"


def test_gui_delete_last_cell_keeps_one(qapp, window):
    window._delete_cell(window.cells[0])
    assert len(window.cells) == 1  # never fewer than one cell


def test_gui_move_cell_down(qapp, window):
    window.cells[0].input.setPlainText("x = 1;")
    c1 = window._add_cell()
    c1.input.setPlainText("y = 2;")
    window._move_cell(window.cells[0], +1)
    assert window.cells[0].text().strip() == "y = 2;"
    assert window.cells[1].text().strip() == "x = 1;"
