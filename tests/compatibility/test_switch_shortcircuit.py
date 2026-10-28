"""Tests for switch/case and short-circuit logical operators."""

from __future__ import annotations

from conftest import run_source, scalar


def test_switch_single_case():
    ns, _ = run_source(
        "x = 2;\nswitch x\n case 1\n  r = 'one';\n case 2\n  r = 'two';\n otherwise\n  r = 'other';\nend\n"
    )
    assert ns["r"] == "two"


def test_switch_otherwise():
    ns, _ = run_source(
        "x = 99;\nswitch x\n case 1\n  r = 'one';\n otherwise\n  r = 'other';\nend\n"
    )
    assert ns["r"] == "other"


def test_switch_cell_list():
    ns, _ = run_source(
        "x = 4;\nswitch x\n case {3, 4}\n  r = 'match';\n otherwise\n  r = 'no';\nend\n"
    )
    assert ns["r"] == "match"


def test_short_circuit_and_skips_right():
    # The right operand would raise if evaluated (1/0), but && short-circuits.
    ns, out = run_source("a = 0 && (1/0);\n")
    assert scalar(ns, "a") == 0


def test_short_circuit_or_skips_right():
    ns, _ = run_source("a = 1 || (1/0);\n")
    assert scalar(ns, "a") == 1


def test_short_circuit_evaluates_right_when_needed():
    ns, _ = run_source("a = 1 && 2;\nb = 0 || 3;\n")
    assert scalar(ns, "a") == 1
    assert scalar(ns, "b") == 1
