"""A Qt6 notebook-style GUI REPL for MALT, styled after macOS.

Run with ``malt gui``. Unlike the terminal REPL, this is a Jupyter-like
*notebook*: every input is an editable cell, you can click back into any
previous cell to edit it, and re-running a cell replaces its output while
sharing one persistent workspace.

The Qt6 platform plugins are not exposed by Nix on their own, so the flake
exports ``MALT_QT6_PLUGIN_PATH``; we forward it to
``QT_QPA_PLATFORM_PLUGIN_PATH`` before importing Qt.
"""

from __future__ import annotations

import io
import os
import re
import sys
import time
from contextlib import redirect_stderr, redirect_stdout
from typing import Any, cast

# Must run before importing PyQt6.
if os.environ.get("MALT_QT6_PLUGIN_PATH"):
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = os.environ["MALT_QT6_PLUGIN_PATH"]

# Quiet the repetitive Qt Wayland text-input v3 warnings (cosmetic only).
_rules = os.environ.get("QT_LOGGING_RULES", "")
_suppress = "qt.qpa.wayland.textinput=false"
os.environ["QT_LOGGING_RULES"] = f"{_rules};{_suppress}" if _rules else _suppress

# The notebook embeds interactive Matplotlib figures, so select the Qt6 Agg
# backend (via PyQt6) before the MALT runtime imports pyplot with its Agg
# default. This only affects `malt gui` — the CLI still honors MPLBACKEND.
os.environ["QT_API"] = "PyQt6"
os.environ["MPLBACKEND"] = "QtAgg"

import matplotlib  # noqa: E402

matplotlib.use("QtAgg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.backends.backend_qtagg import (  # noqa: E402
    FigureCanvasQTAgg,
    NavigationToolbar2QT,
)
from PyQt6.QtCore import QPoint, QStringListModel, Qt, QTimer, pyqtSignal  # noqa: E402
from PyQt6.QtGui import (  # noqa: E402
    QColor,
    QFont,
    QIcon,
    QKeySequence,
    QPainter,
    QPixmap,
    QShortcut,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextCursor,
)
from PyQt6.QtWidgets import (  # noqa: E402
    QApplication,
    QCompleter,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .builtins import BUILTINS  # noqa: E402
from .executor import make_namespace  # noqa: E402
from .repl.session import Repl  # noqa: E402
from .runtime.arrays import as_array  # noqa: E402

_TRAFFIC_RED = "#ff5f57"
_TRAFFIC_YELLOW = "#febc2e"
_TRAFFIC_GREEN = "#28c840"

# Autocompletion vocabulary: builtins plus control keywords and constants.
_COMPLETION_KEYWORDS = (
    "if", "else", "elseif", "for", "while", "end", "break", "continue",
    "return", "function", "switch", "case", "otherwise", "try", "catch",
    "global", "parfor",
)
_COMPLETION_CONSTANTS = ("pi", "eps", "Inf", "NaN", "true", "false", "i", "j")
_BASE_COMPLETIONS = sorted(
    set(BUILTINS) | set(_COMPLETION_KEYWORDS) | set(_COMPLETION_CONSTANTS)
)

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
QScrollArea {
    border: none;
    background: transparent;
}
#Cell {
    background-color: #ffffff;
    border: 1px solid #e4e4e9;
    border-radius: 12px;
}
#Cell:hover {
    border-color: #c7c7ce;
    background-color: #fefefe;
}
#CellPrompt {
    font-family: "SF Mono", "Menlo", "Consolas", monospace;
    font-size: 11px;
    font-weight: 600;
    color: #86868b;
}
#CellInput {
    border: none;
    background: transparent;
    font-family: "SF Mono", "Menlo", "Consolas", monospace;
    font-size: 14px;
    color: #1d1d1f;
}
#CellOutput {
    border: none;
    background-color: #fafafa;
    border-radius: 8px;
    padding: 8px;
    font-family: "SF Mono", "Menlo", "Consolas", monospace;
    font-size: 13px;
    color: #1d1d1f;
}
#FigureOutput {
    background-color: #ffffff;
    border: 1px solid #e4e4e9;
    border-radius: 10px;
}
#FigureToolbar {
    background-color: #f7f7f9;
    border: none;
    border-bottom: 1px solid #e4e4e9;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    padding: 2px 4px;
}
#ResizeHandle {
    background-color: transparent;
    border-top: 1px solid #e4e4e9;
    border-bottom-left-radius: 10px;
    border-bottom-right-radius: 10px;
}
#ResizeHandle:hover {
    background-color: #eef3fb;
}
#RunButton {
    border: none;
    background: transparent;
    color: #0a84ff;
    font-size: 12px;
    font-weight: 700;
}
#CellToolButton {
    border: none;
    background: transparent;
    color: #86868b;
    font-size: 11px;
    font-weight: 600;
}
#CellToolButton:hover {
    color: #1d1d1f;
}
#NewCellButton {
    border: none;
    background: transparent;
    color: #86868b;
    font-size: 15px;
    font-weight: 600;
}
#RunAllButton {
    border: none;
    background: transparent;
    color: #0a84ff;
    font-size: 12px;
    font-weight: 700;
    padding: 4px 8px;
    border-radius: 6px;
}
#RunAllButton:hover {
    background-color: #eef3fb;
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


def _cell_button(text: str, tooltip: str) -> QPushButton:
    b = QPushButton(text)
    b.setObjectName("CellToolButton")
    b.setFixedSize(20, 18)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setToolTip(tooltip)
    return b


def _find_logo() -> str | None:
    """Locate ``assets/logo.png`` (CWD or relative to the package)."""
    candidates = (
        os.path.join("assets", "logo.png"),
        os.path.join(os.path.dirname(__file__), "..", "..", "assets", "logo.png"),
    )
    for path in candidates:
        if os.path.isfile(path):
            return os.path.abspath(path)
    return None


# ---------------------------------------------------------------------------
# Syntax highlighting
# ---------------------------------------------------------------------------

_HIGHLIGHT_COLORS = {
    "keyword": QColor("#9b2393"),
    "string": QColor("#c41a16"),
    "number": QColor("#272ad8"),
    "comment": QColor("#536579"),
}

_HIGHLIGHT_RE: list[tuple[str, re.Pattern[str]]] = [
    ("comment", re.compile(r"%.*")),
    ("string", re.compile(r"'(?:[^']|'')*'")),
    ("number", re.compile(r"\b\d+\.?\d*(?:[eE][+-]?\d+)?[ij]?\b")),
    (
        "keyword",
        re.compile(
            r"\b(?:if|else|elseif|for|while|end|function|switch|case|otherwise|"
            r"try|catch|break|continue|return|global|parfor)\b"
        ),
    ),
]


def tokenize_highlight(text: str) -> list[tuple[int, int, str]]:
    """Return ``(start, length, kind)`` spans for MATLAB syntax highlighting."""
    spans: list[tuple[int, int, str]] = []
    for kind, regex in _HIGHLIGHT_RE:
        for m in regex.finditer(text):
            spans.append((m.start(), m.end() - m.start(), kind))
    spans.sort()
    return spans


class _Highlighter(QSyntaxHighlighter):
    # NOTE: QSyntaxHighlighter.setFormat is broken in Qt 6.12 (formats are
    # silently dropped), so this class is kept only for API compatibility;
    # _CellInput uses _apply_highlighting instead.
    def highlightBlock(self, text: str) -> None:  # noqa: N802
        for start, length, kind in tokenize_highlight(text):
            fmt = QTextCharFormat()
            fmt.setForeground(_HIGHLIGHT_COLORS[kind])
            if kind == "keyword":
                fmt.setFontWeight(QFont.Weight.Bold)
            self.setFormat(start, length, fmt)


def _apply_highlighting(doc: Any) -> None:
    """Apply MATLAB syntax highlighting to a document via QTextCursor.

    (Works around the Qt 6.12 QSyntaxHighlighter regression.)
    """
    text = doc.toPlainText()
    reset = QTextCursor(doc)
    reset.select(QTextCursor.SelectionType.Document)
    reset.setCharFormat(QTextCharFormat())
    for start, length, kind in tokenize_highlight(text):
        fmt = QTextCharFormat()
        fmt.setForeground(_HIGHLIGHT_COLORS[kind])
        if kind == "keyword":
            fmt.setFontWeight(QFont.Weight.Bold)
        cur = QTextCursor(doc)
        cur.setPosition(start)
        cur.setPosition(start + length, QTextCursor.MoveMode.KeepAnchor)
        cur.mergeCharFormat(fmt)


class _CellInput(QPlainTextEdit):
    """A multi-line editor with autocompletion, run shortcuts, and auto-grow.

    Autocompletion is LSP-style: builtins, keywords, constants, and live
    workspace variables, shown as a popup as you type.
    """

    run_inplace = pyqtSignal()
    run_and_next = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self._highlighting = False
        self.textChanged.connect(self._on_text_changed)

        self._completion_model = QStringListModel(_BASE_COMPLETIONS, self)
        self._completer = QCompleter(self._completion_model, self)
        self._completer.setWidget(self)
        self._completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self._completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._completer.activated.connect(self._insert_completion)

    def _on_text_changed(self) -> None:
        self._resize_to_fit()
        self._apply_highlight()
        self._maybe_complete()

    def _apply_highlight(self) -> None:
        if self._highlighting:
            return
        self._highlighting = True
        try:
            _apply_highlighting(self.document())
        finally:
            self._highlighting = False

    def set_completions(self, words: set[str]) -> None:
        self._completion_model.setStringList(
            sorted(set(words) | set(_BASE_COMPLETIONS))
        )

    def _word_under_cursor(self) -> tuple[str, int]:
        cursor = self.textCursor()
        line = cursor.block().text()
        pos = cursor.positionInBlock()
        start = pos
        while start > 0 and (line[start - 1].isalnum() or line[start - 1] == "_"):
            start -= 1
        return line[start:pos], start

    def _maybe_complete(self) -> None:
        word, _ = self._word_under_cursor()
        if len(word) < 2:
            self._completer.popup().hide()
            return
        self._completer.setCompletionPrefix(word)
        if self._completer.completionCount() == 0:
            self._completer.popup().hide()
            return
        rect = self.cursorRect()
        rect.setWidth(
            self._completer.popup().sizeHintForColumn(0)
            + self._completer.popup().verticalScrollBar().sizeHint().width()
        )
        self._completer.complete(rect)

    def _insert_completion(self, text: str) -> None:
        cursor = self.textCursor()
        _, start = self._word_under_cursor()
        cursor.movePosition(
            cursor.MoveOperation.Left,
            cursor.MoveMode.KeepAnchor,
            cursor.positionInBlock() - start,
        )
        cursor.insertText(text)
        self.setTextCursor(cursor)

    def _resize_to_fit(self) -> None:
        line_h = self.fontMetrics().lineSpacing()
        h = self.document().blockCount() * line_h + 20
        h = max(46, min(h, 800))
        if abs(self.height() - h) > 2:
            self.setFixedHeight(h)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._resize_to_fit()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        key = event.key()
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            mods = event.modifiers()
            shift = bool(mods & Qt.KeyboardModifier.ShiftModifier)
            ctrl = bool(
                mods
                & (
                    Qt.KeyboardModifier.ControlModifier
                    | Qt.KeyboardModifier.MetaModifier
                )
            )
            if ctrl and not shift:
                self.run_inplace.emit()
                return
            if shift:
                self.run_and_next.emit()
                return
        super().keyPressEvent(event)


def _force_dark_icons(toolbar: NavigationToolbar2QT) -> None:
    """Recolor matplotlib's toolbar icons dark so they read on a light theme
    (matplotlib otherwise inherits the OS theme and can render white icons)."""
    color = QColor("#3a3a3f")
    for action in toolbar.actions():
        icon = action.icon()
        if icon.isNull():
            continue
        recolored = QIcon()
        sizes = icon.availableSizes() or [toolbar.iconSize()]
        for size in sizes:
            pm = icon.pixmap(size)
            if pm.isNull():
                continue
            painter = QPainter(pm)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            painter.fillRect(pm.rect(), color)
            painter.end()
            recolored.addPixmap(pm)
        if not recolored.isNull():
            action.setIcon(recolored)


class FigureWidget(QFrame):
    """A Matplotlib ``FigureCanvasQTAgg`` with a toolbar and a drag-resize handle."""

    def __init__(self, canvas: FigureCanvasQTAgg) -> None:
        super().__init__()
        self.setObjectName("FigureOutput")
        self.canvas = canvas
        self._drag_start_y: float | None = None
        self._drag_start_h = 0
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.toolbar = NavigationToolbar2QT(canvas, self)
        self.toolbar.setObjectName("FigureToolbar")
        _force_dark_icons(self.toolbar)
        layout.addWidget(self.toolbar)
        canvas.setMinimumWidth(240)
        canvas.setFixedHeight(300)
        layout.addWidget(canvas)

        self._handle = QFrame()
        self._handle.setObjectName("ResizeHandle")
        self._handle.setFixedHeight(7)
        self._handle.setCursor(Qt.CursorShape.SizeVerCursor)
        self._handle.setToolTip("Drag to resize the figure")
        self._handle.mousePressEvent = self._handle_press
        self._handle.mouseMoveEvent = self._handle_move
        self._handle.mouseReleaseEvent = self._handle_release
        layout.addWidget(self._handle)

    def _handle_press(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_y = event.globalPosition().y()
            self._drag_start_h = self.canvas.height()

    def _handle_move(self, event) -> None:
        if self._drag_start_y is not None:
            dy = event.globalPosition().y() - self._drag_start_y
            self.canvas.setFixedHeight(max(140, min(1400, int(self._drag_start_h + dy))))

    def _handle_release(self, event) -> None:
        self._drag_start_y = None


class Cell(QFrame):
    """One editable input cell with an output area and a small toolbar."""

    run_inplace = pyqtSignal(object)
    run_and_next = pyqtSignal(object)
    delete_requested = pyqtSignal(object)
    move_up_requested = pyqtSignal(object)
    move_down_requested = pyqtSignal(object)
    insert_above_requested = pyqtSignal(object)
    insert_below_requested = pyqtSignal(object)

    def __init__(self, number: int) -> None:
        super().__init__()
        self.setObjectName("Cell")
        self.number = number
        self.exec_number: int | None = None
        self.figures: set[int] = set()  # figure numbers this cell displays
        self._text = ""
        self._error = ""
        self._elapsed_ms = 0.0
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 12)
        layout.setSpacing(8)

        header = QHBoxLayout()
        header.setSpacing(4)
        self.prompt = QLabel("In [ ]:")
        self.prompt.setObjectName("CellPrompt")
        header.addWidget(self.prompt)
        header.addStretch(1)
        for text, tip, signal in (
            ("⤒", "Insert cell above", self.insert_above_requested),
            ("⤓", "Insert cell below", self.insert_below_requested),
            ("↑", "Move cell up", self.move_up_requested),
            ("↓", "Move cell down", self.move_down_requested),
            ("×", "Delete cell", self.delete_requested),
        ):
            btn = _cell_button(text, tip)
            btn.clicked.connect(lambda _=False, s=signal: s.emit(self))
            header.addWidget(btn)
        run_btn = _cell_button("▶", "Run cell (Ctrl+Enter)")
        run_btn.setObjectName("RunButton")
        run_btn.clicked.connect(lambda: self.run_inplace.emit(self))
        header.addWidget(run_btn)
        layout.addLayout(header)

        self.input = _CellInput()
        self.input.setObjectName("CellInput")
        self.input.setPlaceholderText("enter code…  (Ctrl+Enter run, Shift+Enter run + next)")
        self.input.run_inplace.connect(lambda: self.run_inplace.emit(self))
        self.input.run_and_next.connect(lambda: self.run_and_next.emit(self))
        layout.addWidget(self.input)

        self.output_container = QWidget()
        self.output_container.setObjectName("CellOutputArea")
        self._output_layout = QVBoxLayout(self.output_container)
        self._output_layout.setContentsMargins(0, 0, 0, 0)
        self._output_layout.setSpacing(8)
        self.output_container.hide()
        layout.addWidget(self.output_container)

        self.text_output = QPlainTextEdit()
        self.text_output.setObjectName("CellOutput")
        self.text_output.setReadOnly(True)
        self.text_output.setMaximumHeight(220)
        self.text_output.hide()
        self.error_output = QPlainTextEdit()
        self.error_output.setObjectName("CellOutput")
        self.error_output.setReadOnly(True)
        self.error_output.setMaximumHeight(220)
        self.error_output.hide()

    def mark_run(self, n: int) -> None:
        self.exec_number = n
        self.prompt.setText(f"In [{n}]:")

    def text(self) -> str:
        return self.input.toPlainText()

    def _clear_output_layout(self) -> None:
        while self._output_layout.count():
            item = self._output_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.hide()

    def render_output(self, figures: list[FigureWidget]) -> None:
        self._clear_output_layout()
        if self._text:
            self.text_output.setPlainText(self._text)
            self.text_output.setStyleSheet("#CellOutput { color: #1d1d1f; background-color: #fafafa; }")
            self._output_layout.addWidget(self.text_output)
            self.text_output.show()
        if self._error:
            self.error_output.setPlainText(self._error)
            self.error_output.setStyleSheet("#CellOutput { color: #d70015; background-color: #fafafa; }")
            self._output_layout.addWidget(self.error_output)
            self.error_output.show()
        for fw in figures:
            self._output_layout.addWidget(fw)
            fw.show()
        self.output_container.setVisible(bool(self._text or self._error or figures))

    def clear_output(self) -> None:
        self._text = ""
        self._error = ""
        self.figures.clear()
        self._clear_output_layout()
        self.output_container.hide()

    def focus_input(self) -> None:
        self.input.setFocus()
        cur = self.input.textCursor()
        cur.movePosition(cur.MoveOperation.End)
        self.input.setTextCursor(cur)


class _TitleBar(QFrame):
    """A frameless title bar that initiates a native window drag."""

    def __init__(self, window: QMainWindow) -> None:
        super().__init__()
        self.setObjectName("TitleBar")
        self.setFixedHeight(40)
        self._window = window
        self._drag_origin: QPoint | None = None

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            handle = self._window.windowHandle()
            if handle is not None and handle.startSystemMove():
                return
            self._drag_origin = event.globalPosition().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self._drag_origin is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self._window.move(
                self._window.pos()
                + event.globalPosition().toPoint()
                - self._drag_origin
            )
            self._drag_origin = event.globalPosition().toPoint()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        self._drag_origin = None
        super().mouseReleaseEvent(event)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.repl = Repl()
        self.cells: list[Cell] = []
        self._counter = 0
        self._exec_count = 0
        self._figure_widgets: dict[int, FigureWidget] = {}
        self.setWindowTitle("MALT")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        logo = _find_logo()
        if logo:
            self.setWindowIcon(QIcon(logo))
        self.resize(980, 680)
        self._build_ui()
        self._add_cell()

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

        notebook = self._build_notebook()
        workspace = QTreeWidget()
        workspace.setObjectName("Workspace")
        workspace.setHeaderLabels(["Name", "Size", "Class"])
        workspace.setRootIsDecorated(False)
        workspace.setColumnWidth(0, 140)
        workspace.setColumnWidth(1, 90)
        self._workspace = workspace

        splitter.addWidget(notebook)
        splitter.addWidget(workspace)
        splitter.setSizes([640, 260])
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        body.addWidget(splitter, 1)
        outer.addWidget(content, 1)

        self._status = QLabel("ready")
        self._status.setObjectName("StatusBar")
        self._status.setContentsMargins(16, 0, 16, 8)
        outer.addWidget(self._status)

        QShortcut(QKeySequence("Ctrl+L"), self, activated=self._clear_outputs)

    def _build_notebook(self) -> QScrollArea:
        self._container = QWidget()
        self._container.setObjectName("Content")
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(0, 0, 8, 0)
        self._layout.setSpacing(12)
        self._layout.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._container)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._scroll = scroll
        return scroll

    def _build_title_bar(self) -> QWidget:
        bar = _TitleBar(self)
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

        logo = _find_logo()
        if logo:
            icon = QLabel()
            icon.setPixmap(
                QPixmap(logo).scaledToHeight(
                    20, Qt.TransformationMode.SmoothTransformation
                )
            )
            icon.setFixedHeight(20)
            layout.addWidget(icon)

        title = QLabel("MALT")
        title.setObjectName("TitleLabel")
        layout.addWidget(title)
        layout.addStretch(1)

        run_all_btn = QPushButton("▶▶ Run all")
        run_all_btn.setObjectName("RunAllButton")
        run_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        run_all_btn.setToolTip("Reset the workspace and run every cell")
        run_all_btn.clicked.connect(self._run_all)
        layout.addWidget(run_all_btn)

        new_btn = QPushButton("＋")
        new_btn.setObjectName("NewCellButton")
        new_btn.setFixedSize(28, 24)
        new_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        new_btn.setToolTip("New cell")
        new_btn.clicked.connect(self._add_cell)
        layout.addWidget(new_btn)

        return bar

    # -- cells --------------------------------------------------------------
    def _new_cell(self) -> Cell:
        self._counter += 1
        cell = Cell(self._counter)
        cell.run_inplace.connect(self._run_cell_inplace)
        cell.run_and_next.connect(self._run_cell_and_next)
        cell.delete_requested.connect(self._delete_cell)
        cell.move_up_requested.connect(lambda c, d=-1: self._move_cell(c, d))
        cell.move_down_requested.connect(lambda c, d=+1: self._move_cell(c, d))
        cell.insert_above_requested.connect(self._insert_above)
        cell.insert_below_requested.connect(self._insert_below)
        return cell

    def _add_cell(self) -> Cell:
        cell = self._new_cell()
        self._layout.insertWidget(self._layout.count() - 1, cell)
        self.cells.append(cell)
        cell.focus_input()
        return cell

    def _insert_above(self, cell: Cell) -> None:
        self._insert_cell_at(self.cells.index(cell))

    def _insert_below(self, cell: Cell) -> None:
        self._insert_cell_at(self.cells.index(cell) + 1)

    def _insert_cell_at(self, idx: int) -> Cell:
        cell = self._new_cell()
        self.cells.insert(idx, cell)
        self._relayout()
        cell.focus_input()
        return cell

    def _relayout(self) -> None:
        for c in self.cells:
            self._layout.removeWidget(c)
        for c in self.cells:
            self._layout.insertWidget(self._layout.count() - 1, c)

    def _delete_cell(self, cell: Cell) -> None:
        if cell not in self.cells:
            return
        # The cell owns its figure widgets as children; drop our references so
        # a later "Run all" doesn't try to delete already-destroyed widgets.
        for f in list(cell.figures):
            self._figure_widgets.pop(f, None)
        self.cells.remove(cell)
        self._layout.removeWidget(cell)
        cell.deleteLater()
        if not self.cells:
            self._add_cell()

    def _move_cell(self, cell: Cell, delta: int) -> None:
        idx = self.cells.index(cell)
        new_idx = idx + delta
        if new_idx < 0 or new_idx >= len(self.cells):
            return
        self.cells.pop(idx)
        self.cells.insert(new_idx, cell)
        self._relayout()

    def _run_cell_inplace(self, cell: Cell) -> None:
        self._execute(cell, move_next=False)

    def _run_cell_and_next(self, cell: Cell) -> None:
        self._execute(cell, move_next=True)

    def _eval_into(self, cell: Cell, text: str) -> str | None:
        start = time.perf_counter()
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            action = self.repl._handle(text)
        cell._text = out.getvalue()
        cell._error = err.getvalue()
        cell._elapsed_ms = (time.perf_counter() - start) * 1000
        return action

    def _run_text(self, cell: Cell, text: str) -> str | None:
        self._exec_count += 1
        cell.mark_run(self._exec_count)
        return self._eval_into(cell, text)

    # -- figure management --------------------------------------------------
    def _figure_widget(self, fig_num: int) -> FigureWidget:
        fw = self._figure_widgets.get(fig_num)
        if fw is None:
            fig = plt.figure(fig_num)
            fw = FigureWidget(cast(FigureCanvasQTAgg, fig.canvas))
            self._figure_widgets[fig_num] = fw
        return fw

    def _close_figure(self, fig_num: int) -> None:
        fw = self._figure_widgets.pop(fig_num, None)
        if fw is not None:
            self._safe_delete_later(fw)

    @staticmethod
    def _safe_delete_later(widget: QWidget) -> None:
        try:
            widget.deleteLater()
        except RuntimeError:
            pass  # C++ object already destroyed (e.g. its parent cell was deleted)

    def _sync_figures(self, cell: Cell, before: set[int], after: set[int]) -> None:
        for f in before - after:
            self._close_figure(f)
            for c in self.cells:
                c.figures.discard(f)
        for f in after - before:
            cell.figures.add(f)
            self._figure_widget(f)
        for fw in self._figure_widgets.values():
            fw.canvas.draw_idle()

    def _render_cell(self, cell: Cell) -> None:
        widgets = [
            self._figure_widgets[f] for f in sorted(cell.figures) if f in self._figure_widgets
        ]
        cell.render_output(widgets)

    def _render_all_cells(self) -> None:
        for c in self.cells:
            self._render_cell(c)

    def _execute(self, cell: Cell, move_next: bool) -> None:
        text = cell.text().strip()
        if text:
            before = set(plt.get_fignums())
            action = self._run_text(cell, text)
            after = set(plt.get_fignums())
            self._sync_figures(cell, before, after)
            self._refresh_workspace()
            self._status.setText(
                f"{len(self.repl.namespace)} names · last run {cell._elapsed_ms:.1f} ms"
            )
            self._render_all_cells()
            self._flash_cell(cell)
            if action == "quit":
                self.close()
                return
        else:
            cell._text = ""
            cell._error = ""
            self._render_all_cells()
        if move_next:
            idx = self.cells.index(cell)
            if idx == len(self.cells) - 1:
                self._add_cell()
            else:
                self.cells[idx + 1].focus_input()
        self._scroll_to_bottom()

    def _flash_cell(self, cell: Cell) -> None:
        """Briefly highlight the cell border to give execution feedback."""
        cell.setStyleSheet(
            "#Cell { background-color: #f4f8ff; border: 1px solid #0a84ff; "
            "border-radius: 12px; }"
        )
        QTimer.singleShot(400, lambda: cell.setStyleSheet(""))

    def _run_all(self) -> None:
        self.repl.namespace = make_namespace()
        plt.close("all")
        for fw in self._figure_widgets.values():
            self._safe_delete_later(fw)
        self._figure_widgets.clear()
        for cell in self.cells:
            cell.figures.clear()
            cell._text = ""
            cell._error = ""
        for cell in self.cells:
            text = cell.text().strip()
            if text:
                before = set(plt.get_fignums())
                action = self._run_text(cell, text)
                after = set(plt.get_fignums())
                self._sync_figures(cell, before, after)
                if action == "quit":
                    break
        self._refresh_workspace()
        self._status.setText(f"{len(self.repl.namespace)} names in workspace")
        self._render_all_cells()
        self._scroll_to_bottom()

    def _scroll_to_bottom(self) -> None:
        bar = self._scroll.verticalScrollBar()
        bar.setValue(bar.maximum())

    def _clear_outputs(self) -> None:
        plt.close("all")
        for fw in self._figure_widgets.values():
            self._safe_delete_later(fw)
        self._figure_widgets.clear()
        for c in self.cells:
            c._text = ""
            c._error = ""
            c.figures.clear()
            c._clear_output_layout()
            c.output_container.hide()

    # -- title-bar drag -----------------------------------------------------
    def _toggle_maximize(self) -> None:
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    # -- workspace sidebar --------------------------------------------------
    def _refresh_workspace(self) -> None:
        self._workspace.clear()
        entries: list[tuple[str, str, str]] = []
        names: set[str] = set()
        for name in sorted(self.repl.namespace):
            if name.startswith("_"):
                continue
            names.add(name)
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
        for cell in self.cells:
            cell.input.set_completions(names)


def run() -> int:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(_STYLESHEET)
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run())
