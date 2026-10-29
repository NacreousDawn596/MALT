"""A Qt6 GUI REPL for MALT, styled after macOS.

Run with ``malt gui``. Reuses the same evaluation core as the terminal REPL
(:class:`malt.repl.session.Repl`) and adds an Apple-like window: a frameless
title bar with traffic lights, a console, an input field, and a live workspace
sidebar.

The Qt6 platform plugins are not exposed by Nix on their own, so the flake
exports ``MALT_QT6_PLUGIN_PATH``; we forward it to
``QT_QPA_PLATFORM_PLUGIN_PATH`` before importing Qt.
"""

from __future__ import annotations

import io
import os
import sys
from contextlib import redirect_stderr, redirect_stdout

# Must run before importing PyQt6.
if os.environ.get("MALT_QT6_PLUGIN_PATH"):
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = os.environ["MALT_QT6_PLUGIN_PATH"]

import numpy as np  # noqa: E402
from PyQt6.QtCore import QPoint, Qt  # noqa: E402
from PyQt6.QtGui import QColor, QFont, QKeySequence, QShortcut  # noqa: E402
from PyQt6.QtWidgets import (  # noqa: E402
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .repl.session import Repl, _is_incomplete  # noqa: E402
from .runtime.arrays import as_array  # noqa: E402

_TRAFFIC_RED = "#ff5f57"
_TRAFFIC_YELLOW = "#febc2e"
_TRAFFIC_GREEN = "#28c840"

_STYLESHEET = """
* {
    font-family: "SF Pro Display", "Segoe UI", "Helvetica Neue", sans-serif;
    font-size: 14px;
    color: #1d1d1f;
}
QMainWindow, #Content {
    background-color: #f5f5f7;
}
#TitleBar {
    background-color: #f5f5f7;
    border-bottom: 1px solid #e4e4e9;
}
#TitleLabel {
    font-size: 13px;
    font-weight: 600;
    color: #6e6e73;
}
#Console {
    background-color: #ffffff;
    border: 1px solid #e4e4e9;
    border-radius: 12px;
    padding: 10px;
    font-family: "SF Mono", "Menlo", "Consolas", monospace;
    font-size: 13px;
    color: #1d1d1f;
}
#Input {
    background-color: #ffffff;
    border: 1px solid #e4e4e9;
    border-radius: 10px;
    padding: 8px 12px;
    font-family: "SF Mono", "Menlo", "Consolas", monospace;
    font-size: 14px;
    color: #1d1d1f;
}
#Input:focus {
    border: 2px solid #0a84ff;
    padding: 7px 11px;
}
#Prompt {
    font-family: "SF Mono", "Menlo", "Consolas", monospace;
    font-size: 14px;
    font-weight: 700;
    color: #0a84ff;
}
#Workspace {
    background-color: #ffffff;
    border: 1px solid #e4e4e9;
    border-radius: 12px;
    font-size: 12px;
    color: #1d1d1f;
}
QHeaderView::section {
    background-color: #f5f5f7;
    border: none;
    padding: 4px;
    font-weight: 600;
    color: #6e6e73;
}
#StatusBar {
    color: #86868b;
    font-size: 11px;
    background: transparent;
}
QPushButton#Traffic {
    border: none;
    border-radius: 7px;
    min-width: 12px;
    max-width: 12px;
    min-height: 12px;
    max-height: 12px;
}
"""


def _traffic_button(color: str) -> QPushButton:
    b = QPushButton()
    b.setObjectName("Traffic")
    b.setStyleSheet(f"QPushButton#Traffic {{ background-color: {color}; }}")
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setFixedSize(12, 12)
    return b


class _HistoryLineEdit(QLineEdit):
    """A single-line editor with Up/Down history navigation."""

    def __init__(self) -> None:
        super().__init__()
        self._history: list[str] = []
        self._cursor = 0

    def commit(self, text: str) -> None:
        if text and (not self._history or self._history[-1] != text):
            self._history.append(text)
        self._cursor = len(self._history)

    def keyPressEvent(self, event) -> None:  # noqa: N802
        key = event.key()
        if key == Qt.Key.Key_Up:
            if self._history and self._cursor > 0:
                self._cursor -= 1
                self.setText(self._history[self._cursor])
            return
        if key == Qt.Key.Key_Down:
            if self._cursor < len(self._history) - 1:
                self._cursor += 1
                self.setText(self._history[self._cursor])
            else:
                self._cursor = len(self._history)
                self.clear()
            return
        super().keyPressEvent(event)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.repl = Repl()
        self._buffer = ""
        self.setWindowTitle("MALT")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.resize(920, 620)
        self._build_ui()
        self._append_output("MALT — MATLAB-compatible runtime\n", kind="banner")
        self._append_output(
            "Type an expression, or 'help' for commands, 'exit' to quit.\n\n", kind="dim"
        )

    # -- UI construction ----------------------------------------------------
    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("Content")
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        outer.addWidget(self._build_title_bar())

        content = QWidget()
        body = QVBoxLayout(content)
        body.setContentsMargins(16, 16, 16, 12)
        body.setSpacing(12)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        console = QPlainTextEdit()
        console.setObjectName("Console")
        console.setReadOnly(True)
        console.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self._console = console

        workspace = QTreeWidget()
        workspace.setObjectName("Workspace")
        workspace.setHeaderLabels(["Name", "Size", "Class"])
        workspace.setRootIsDecorated(False)
        workspace.setColumnWidth(0, 140)
        workspace.setColumnWidth(1, 90)
        self._workspace = workspace

        splitter.addWidget(console)
        splitter.addWidget(workspace)
        splitter.setSizes([620, 260])
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        body.addWidget(splitter, 1)
        body.addWidget(self._build_input_row())

        outer.addWidget(content, 1)
        self._status = QLabel("ready")
        self._status.setObjectName("StatusBar")
        self._status.setContentsMargins(16, 0, 16, 8)
        outer.addWidget(self._status)

        QShortcut(QKeySequence("Ctrl+L"), self, activated=self._clear_console)

    def _build_title_bar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("TitleBar")
        bar.setFixedHeight(40)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(8)

        close_btn = _traffic_button(_TRAFFIC_RED)
        close_btn.clicked.connect(self.close)
        min_btn = _traffic_button(_TRAFFIC_YELLOW)
        min_btn.clicked.connect(self.showMinimized)
        zoom_btn = _traffic_button(_TRAFFIC_GREEN)
        zoom_btn.clicked.connect(self._toggle_maximize)

        layout.addWidget(close_btn)
        layout.addWidget(min_btn)
        layout.addWidget(zoom_btn)
        layout.addSpacing(12)

        title = QLabel("MALT")
        title.setObjectName("TitleLabel")
        layout.addWidget(title)
        layout.addStretch(1)

        self._drag_origin: QPoint | None = None
        bar.mousePressEvent = self._title_mouse_press
        bar.mouseMoveEvent = self._title_mouse_move
        bar.mouseReleaseEvent = self._title_mouse_release
        return bar

    def _build_input_row(self) -> QWidget:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._prompt = QLabel("»")
        self._prompt.setObjectName("Prompt")
        self._input = _HistoryLineEdit()
        self._input.setObjectName("Input")
        self._input.setPlaceholderText("enter an expression…")
        self._input.returnPressed.connect(self._submit)

        layout.addWidget(self._prompt)
        layout.addWidget(self._input, 1)
        return row

    # -- title-bar drag -----------------------------------------------------
    def _title_mouse_press(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_origin = event.globalPosition().toPoint()

    def _title_mouse_move(self, event) -> None:
        if self._drag_origin is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(self.pos() + event.globalPosition().toPoint() - self._drag_origin)
            self._drag_origin = event.globalPosition().toPoint()

    def _title_mouse_release(self, event) -> None:
        self._drag_origin = None

    def _toggle_maximize(self) -> None:
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    # -- console output -----------------------------------------------------
    def _append_output(self, text: str, kind: str = "normal") -> None:
        cur = self._console.textCursor()
        cur.movePosition(cur.MoveOperation.End)
        fmt = cur.charFormat()
        if kind == "input":
            fmt.setForeground(QColor("#0a84ff"))
            fmt.setFontWeight(QFont.Weight.Bold)
        elif kind == "error":
            fmt.setForeground(QColor("#d70015"))
        elif kind == "banner":
            fmt.setFontWeight(QFont.Weight.Bold)
        elif kind == "dim":
            fmt.setForeground(QColor("#86868b"))
        else:
            fmt.setForeground(QColor("#1d1d1f"))
        cur.setCharFormat(fmt)
        cur.insertText(text)
        self._console.setTextCursor(cur)
        self._console.ensureCursorVisible()

    def _clear_console(self) -> None:
        self._console.clear()

    # -- input / evaluation -------------------------------------------------
    def _set_prompt(self, marker: str) -> None:
        self._prompt.setText(marker)

    def _submit(self) -> None:
        line = self._input.text()
        self._input.clear()
        self._input.commit(line)

        if self._buffer:
            marker = "…"
            self._buffer += "\n" + line
        else:
            marker = "»"
            self._buffer = line

        self._append_output(f"{marker} {line}\n", kind="input")

        if _is_incomplete(self._buffer):
            self._set_prompt("…")
            return

        source = self._buffer
        self._buffer = ""
        self._set_prompt("»")

        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            action = self.repl._handle(source)
        if out.getvalue():
            self._append_output(out.getvalue())
        if err.getvalue():
            self._append_output(err.getvalue(), kind="error")
        self._refresh_workspace()
        self._status.setText(f"{len(self.repl.namespace)} names in workspace")
        if action == "quit":
            self.close()

    # -- workspace sidebar --------------------------------------------------
    def _refresh_workspace(self) -> None:
        self._workspace.clear()
        entries: list[tuple[str, str, str]] = []
        for name in sorted(self.repl.namespace):
            if name.startswith("_"):
                continue
            val = self.repl.namespace[name]
            a = as_array(val)
            if isinstance(a, str):
                cls, shape = "char", f"1x{len(a)}"
            elif isinstance(a, np.ndarray):
                cls = "double" if a.dtype.kind in "fc" else str(a.dtype)
                shape = "x".join(str(s) for s in a.shape)
            else:
                cls = type(a).__name__
                shape = "1x1"
            entries.append((name, shape, cls))
        for name, shape, cls in entries:
            QTreeWidgetItem(self._workspace, [name, shape, cls])


def run() -> int:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(_STYLESHEET)
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run())
