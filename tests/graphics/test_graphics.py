"""Graphics compatibility tests: inspect actual Matplotlib artists."""

from __future__ import annotations

import os

import numpy as np
from conftest import run_file

import malt.runtime.graphics as mg

EXAMPLES = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "examples")


def _run(name: str):
    return run_file(os.path.join(EXAMPLES, "graphics", name))


def _figures():
    return mg.all_figures()


def test_g1_sine_plot():
    _run("sine_plot.m")
    assert mg.figure_count() == 1
    fig = mg.current_figure()
    assert len(fig.axes) == 1
    ax = fig.axes[0]
    lines = ax.get_lines()
    assert len(lines) == 1
    x = lines[0].get_xdata()
    y = lines[0].get_ydata()
    assert len(x) == 200
    assert abs(x[0] - 0) < 1e-9
    assert abs(x[-1] - 2 * np.pi) < 1e-6
    np.testing.assert_allclose(y, np.sin(x), atol=1e-10)
    assert ax.get_title() == "Sine Wave"
    assert ax.get_xlabel() == "Time"
    assert ax.get_ylabel() == "Amplitude"
    assert len(ax.get_xgridlines()) > 0 or len(ax.get_ygridlines()) > 0


def test_g2_multiple_lines():
    _run("multiple_lines.m")
    fig = mg.current_figure()
    ax = fig.axes[0]
    lines = ax.get_lines()
    assert len(lines) == 2
    x = lines[0].get_xdata()
    np.testing.assert_allclose(lines[0].get_ydata(), np.sin(x), atol=1e-10)
    np.testing.assert_allclose(lines[1].get_ydata(), np.cos(x), atol=1e-10)
    labels = [t.get_text() for t in ax.get_legend().get_texts()]
    assert labels == ["sin(x)", "cos(x)"]
    assert ax.get_title() == "Trigonometric Functions"


def test_g3_subplots():
    _run("subplots.m")
    fig = mg.current_figure()
    assert len(fig.axes) == 2
    ax1, ax2 = fig.axes
    assert ax1.get_title() == "Square"
    assert ax2.get_title() == "Square Root"
    # ax1 has square curve, ax2 has square-root curve
    y1 = ax1.get_lines()[0].get_ydata()
    y2 = ax2.get_lines()[0].get_ydata()
    x1 = ax1.get_lines()[0].get_xdata()
    x2 = ax2.get_lines()[0].get_xdata()
    np.testing.assert_allclose(y1, x1**2, atol=1e-8)
    np.testing.assert_allclose(y2, np.sqrt(x2), atol=1e-8)


def test_g4_scatter():
    _run("scatter.m")
    fig = mg.current_figure()
    ax = fig.axes[0]
    colls = ax.collections
    assert len(colls) == 1
    offsets = colls[0].get_offsets()
    assert len(offsets) == 5
    np.testing.assert_array_equal(offsets[:, 0], [1, 2, 3, 4, 5])
    np.testing.assert_array_equal(offsets[:, 1], [1, 4, 9, 16, 25])


def test_g5_histogram():
    _run("histogram.m")
    fig = mg.current_figure()
    ax = fig.axes[0]
    patches = [p for p in ax.patches if hasattr(p, "get_height")]
    assert len(patches) >= 1
    # total count equals 8 samples
    heights = sum(p.get_height() for p in patches)
    assert heights == 8


def test_g6_surface():
    _run("surface.m")
    fig = mg.current_figure()
    ax = fig.axes[0]
    # 3D axes have a plot_surface collection
    assert len(ax.collections) >= 1
    assert ax.get_xlabel() == "X"
    assert ax.get_ylabel() == "Y"
    assert ax.get_title() == "3D Surface"


def test_g7_imagesc():
    _run("imagesc.m")
    fig = mg.current_figure()
    ax = fig.axes[0]
    assert len(ax.images) >= 1
    img = ax.images[0]
    data = np.asarray(img.get_array())
    assert data.shape == (50, 50)


def test_g8_save_figure(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _run("save_figure.m")
    out = tmp_path / "test_plot.png"
    assert out.exists()
    assert out.stat().st_size > 0
    # validate PNG header
    with open(out, "rb") as f:
        assert f.read(8) == b"\x89PNG\r\n\x1a\n"


def test_g9_figure_lifecycle():
    from conftest import run_source

    run_source(
        "figure(1);\n"
        "plot(1:10);\n"
        "figure(2);\n"
        "plot(10:-1:1);\n"
        "figure(1);\n"
        "clf;\n"
        "plot(1:5);\n"
    )
    assert mg.figure_count() == 2
    fig1 = mg.all_figures()[0]
    fig2 = mg.all_figures()[1]
    lines1 = fig1.axes[0].get_lines()
    lines2 = fig2.axes[0].get_lines()
    assert len(lines1) == 1
    assert len(lines2) == 1
    np.testing.assert_array_equal(lines1[0].get_ydata(), np.arange(1, 6))
    np.testing.assert_array_equal(lines2[0].get_ydata(), np.arange(10, 0, -1))
