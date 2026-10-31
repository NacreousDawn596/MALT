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
    assert "1" in cell.text_output.toPlainText()
    # Edit and re-run the same cell; output is replaced, not appended.
    cell.input.setPlainText("x = 2")
    window._execute(cell, move_next=False)
    assert window.repl.namespace["x"] == 2
    assert "2" in cell.text_output.toPlainText()
    assert "1" not in cell.text_output.toPlainText()


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


def test_gui_execution_counter(qapp, window):
    cell = window.cells[0]
    cell.input.setPlainText("x = 1;")
    window._execute(cell, move_next=False)
    assert cell.exec_number == 1
    assert cell.prompt.text() == "In [1]:"
    cell.input.setPlainText("x = 2;")
    window._execute(cell, move_next=False)
    assert cell.exec_number == 2
    assert cell.prompt.text() == "In [2]:"


def test_gui_insert_below(qapp, window):
    window.cells[0].input.setPlainText("x = 1;")
    window._insert_below(window.cells[0])
    assert len(window.cells) == 2
    assert window.cells[1].text().strip() == ""  # new empty cell below


def test_gui_insert_above(qapp, window):
    window.cells[0].input.setPlainText("x = 1;")
    window._insert_above(window.cells[0])
    assert len(window.cells) == 2
    assert window.cells[0].text().strip() == ""  # new empty cell above
    assert window.cells[1].text().strip() == "x = 1;"


def test_highlight_tokenizer():
    from malt.gui import tokenize_highlight

    spans = tokenize_highlight("for k = 1:10\n  x = sin(k); % comment\nend")
    kinds = {k for _, _, k in spans}
    assert "keyword" in kinds
    assert "number" in kinds
    assert "comment" in kinds


# ---------------------------------------------------------------------------
# Matplotlib figure embedding
# ---------------------------------------------------------------------------


def _run(window, cell, code):
    cell.input.setPlainText(code)
    window._execute(cell, move_next=False)


def test_gui_figure_renders_in_cell(qapp, window):
    cell = window.cells[0]
    _run(window, cell, "x = linspace(0, 2*pi, 200);\nplot(x, sin(x));\n")
    assert cell.figures == {1}
    assert 1 in window._figure_widgets


def test_gui_multiple_figures(qapp, window):
    cell = window.cells[0]
    _run(window, cell, "figure(1);\nplot(1:10);\nfigure(2);\nplot(1:10);\n")
    assert cell.figures == {1, 2}
    assert set(window._figure_widgets) == {1, 2}


def test_gui_figure_modification_cross_cell(qapp, window):
    c0 = window.cells[0]
    _run(window, c0, "x = linspace(0, 2*pi, 200);\nfigure(1);\nplot(x, sin(x));\n")
    assert c0.figures == {1}
    c1 = window._add_cell()
    _run(window, c1, "hold on;\nplot(x, cos(x));\n")
    # figure 1 stays with the cell that created it; no duplicate canvas
    assert c0.figures == {1}
    assert c1.figures == set()
    assert list(window._figure_widgets) == [1]


def test_gui_figure_close_removes_canvas(qapp, window):
    cell = window.cells[0]
    _run(window, cell, "figure(1);\nplot(1:10);\n")
    assert 1 in window._figure_widgets
    _run(window, cell, "close(1);\n")
    assert 1 not in window._figure_widgets
    assert cell.figures == set()


def test_gui_error_after_plot_preserves_figure(qapp, window):
    cell = window.cells[0]
    _run(window, cell, "plot(1:10);\ndisp(undefined_var);\n")
    # the plot survives even though the second statement errors
    assert cell.figures == {1}
    assert 1 in window._figure_widgets
    assert "undefined" in cell.error_output.toPlainText()


def test_gui_repeated_execution_no_duplicate_canvas(qapp, window):
    cell = window.cells[0]
    _run(window, cell, "plot(1:10);\n")
    _run(window, cell, "plot(1:10);\n")
    assert cell.figures == {1}
    assert list(window._figure_widgets) == [1]


def test_gui_input_autogrows(qapp, window):
    cell = window.cells[0]
    cell.input.setPlainText("x = 1;")
    qapp.processEvents()
    h1 = cell.input.height()
    cell.input.setPlainText("x = 1;\ny = 2;\nz = 3;\nw = 4;")
    qapp.processEvents()
    h2 = cell.input.height()
    assert h2 > h1


def test_gui_figure_has_resize_handle(qapp, window):
    cell = window.cells[0]
    _run(window, cell, "plot(1:10);\n")
    fw = window._figure_widgets[1]
    assert fw._handle is not None
    assert fw.canvas.height() > 0


def test_gui_toolbar_icons_recolored(qapp, window):
    cell = window.cells[0]
    _run(window, cell, "plot(1:10);\n")
    fw = window._figure_widgets[1]
    # Every toolbar action should have a (dark, non-null) icon.
    for action in fw.toolbar.actions():
        if action.text():  # only actions with a label have an icon
            assert not action.icon().isNull()


def test_gui_execution_timing(qapp, window):
    cell = window.cells[0]
    _run(window, cell, "x = 1;\n")
    assert cell._elapsed_ms >= 0.0


def test_gui_autocompletion_builtins(qapp, window):
    cell = window.cells[0]
    comp = cell.input._completer
    comp.setCompletionPrefix("sq")
    assert comp.completionCount() >= 1
    assert "sqrt" in [
        comp.completionModel().index(i, 0).data() for i in range(comp.completionCount())
    ]


def test_gui_autocompletion_workspace_vars(qapp, window):
    cell = window.cells[0]
    window.repl._handle("my_custom_var = 1;")
    window._refresh_workspace()
    comp = cell.input._completer
    comp.setCompletionPrefix("my_custom")
    assert comp.completionCount() == 1
    assert comp.completionModel().index(0, 0).data() == "my_custom_var"


def test_gui_autocompletion_control_functions(qapp, window):
    cell = window.cells[0]
    comp = cell.input._completer
    comp.setCompletionPrefix("ste")
    names = [
        comp.completionModel().index(i, 0).data() for i in range(comp.completionCount())
    ]
    assert "stepinfo" in names


def test_gui_syntax_highlighting_applied(qapp, window):
    from PyQt6.QtGui import QTextCursor

    cell = window.cells[0]
    cell.input.setPlainText("for k = 1:10\n  x = sin(k);\nend")
    qapp.processEvents()
    cur = QTextCursor(cell.input.document())
    cur.setPosition(0)
    cur.setPosition(3, QTextCursor.MoveMode.KeepAnchor)
    fmt = cur.charFormat()
    assert fmt.foreground().color().name() == "#a626a4"  # keyword magenta


def test_gui_autocompletion_typing_flow(qapp, window):
    from PyQt6.QtGui import QTextCursor

    cell = window.cells[0]
    cell.input.insertPlainText("sq")
    cur = cell.input.textCursor()
    cur.movePosition(QTextCursor.MoveOperation.End)
    cell.input.setTextCursor(cur)
    qapp.processEvents()
    comp = cell.input._completer
    assert comp.completionPrefix() == "sq"
    assert comp.completionCount() < 100  # filtered, not the full vocabulary


def test_gui_delete_cell_with_figure_then_run_all(qapp, window):
    c0 = window.cells[0]
    c0.input.setPlainText("plot(1:10);")
    window._execute(c0, move_next=False)
    c1 = window._add_cell()
    c1.input.setPlainText("figure(2); plot(1:20);")
    window._execute(c1, move_next=False)
    window._delete_cell(c0)  # cell 0 owned figure 1
    window._run_all()  # must not crash on a stale FigureWidget
    assert set(window._figure_widgets) <= {1, 2}
