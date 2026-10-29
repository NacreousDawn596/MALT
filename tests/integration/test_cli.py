"""CLI integration tests."""

from __future__ import annotations

import pytest

from malt.cli import main


def test_eval(capsys):
    rc = main(["eval", "2 + 3 * 4"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "14" in out


def test_run_script(tmp_path, capsys):
    f = tmp_path / "script.m"
    f.write_text("a = 1;\nfor k = 1:5\n a = a + k;\nend\ndisp(a);\n")
    rc = main(["run", str(f)])
    assert rc == 0
    assert "16" in capsys.readouterr().out


def test_compile_emits_generated(tmp_path, capsys):
    f = tmp_path / "script.m"
    f.write_text("A = [1 2; 3 4];\n")
    rc = main(["compile", str(f)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "_ml.matrix" in out


def test_compile_to_file(tmp_path):
    f = tmp_path / "script.m"
    f.write_text("A = [1 2; 3 4];\n")
    out = tmp_path / "gen.py"
    rc = main(["compile", str(f), "-o", str(out)])
    assert rc == 0
    assert out.exists()
    assert "_ml.matrix" in out.read_text()


def test_show_generated(tmp_path, capsys):
    f = tmp_path / "script.m"
    f.write_text("a = 2 + 3;\n")
    rc = main(["run", str(f), "--show-generated"])
    assert rc == 0
    assert "_ml.plus" in capsys.readouterr().out


def test_version(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert "malt" in capsys.readouterr().out


def test_error_returns_nonzero(tmp_path, capsys):
    f = tmp_path / "bad.m"
    f.write_text("A = [1 2; 3 4];\ndisp(A(10,1));\n")
    rc = main(["run", str(f)])
    assert rc == 1
    err = capsys.readouterr().err
    assert "bad.m" in err


def test_run_plot_autoshow_is_noop_headless(tmp_path, capsys):
    f = tmp_path / "plot.m"
    f.write_text("plot([1 2 3], [4 5 6]);\n")
    rc = main(["run", str(f)])
    assert rc == 0
    out = capsys.readouterr().out
    # Under the headless Agg backend, auto-show is a silent no-op.
    assert "non-interactive" not in out


def test_show_and_drawnow_are_builtins(tmp_path, capsys):
    f = tmp_path / "show.m"
    f.write_text("plot([1 2 3]);\ndrawnow;\n")
    rc = main(["run", str(f)])
    assert rc == 0


def test_show_compiles_to_show_call(tmp_path, capsys):
    f = tmp_path / "show.m"
    f.write_text("show;\n")
    rc = main(["run", str(f), "--show-generated"])
    assert rc == 0
    assert "_ml.show()" in capsys.readouterr().out


def test_run_error_shows_excerpt(tmp_path, capsys):
    f = tmp_path / "bad.m"
    f.write_text("A = [1 2];\ndisp(A(5));\n")
    rc = main(["run", str(f), "--no-color"])
    assert rc == 1
    err = capsys.readouterr().err
    assert "[E2001]" in err
    assert "disp(A(5))" in err


def test_run_error_json_format(tmp_path, capsys):
    import json

    f = tmp_path / "bad.m"
    f.write_text("disp(undefined_thing);\n")
    rc = main(["run", str(f), "--diagnostic-format", "json"])
    assert rc == 1
    data = json.loads(capsys.readouterr().err)
    assert data["code"] == "E2003"
    assert data["location"]["filename"] == str(f)


def test_run_warning_to_stderr(tmp_path, capsys):
    f = tmp_path / "warn.m"
    f.write_text("sin = 5;\ny = 1;\n")
    rc = main(["run", str(f), "--no-color"])
    assert rc == 0
    err = capsys.readouterr().err
    assert "[W1001]" in err


def test_run_no_warnings_silences(tmp_path, capsys):
    f = tmp_path / "warn.m"
    f.write_text("sin = 5;\n")
    rc = main(["run", str(f), "--no-warnings"])
    assert rc == 0
    assert capsys.readouterr().err == ""


def test_run_werror_fails(tmp_path, capsys):
    f = tmp_path / "warn.m"
    f.write_text("sin = 5;\n")
    rc = main(["run", str(f), "--werror", "--no-color"])
    assert rc == 1
