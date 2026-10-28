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
