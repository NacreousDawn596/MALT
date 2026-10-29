"""V3 source-map generation."""

from __future__ import annotations

import json

from malt.compiler import compile_source
from malt.sourcemap import _BASE64, build_source_map, encode_vlq


def _decode_vlq(s: str, i: int) -> tuple[int, int]:
    value = 0
    shift = 0
    while True:
        digit = _BASE64.index(s[i])
        i += 1
        value |= (digit & 31) << shift
        if digit & 32:
            shift += 5
            continue
        return (value >> 1) if (value & 1) == 0 else -(value >> 1), i


def _decode_mappings(mappings: str) -> list[tuple[int, int, int, int, int]]:
    """Decode a V3 mappings string into (gen_line, gen_col, src, src_line, src_col)."""
    out: list[tuple[int, int, int, int, int]] = []
    src_idx = src_line = src_col = 0
    for gen_line, line in enumerate(mappings.split(";")):
        gen_col = 0
        for seg in line.split(","):
            if not seg:
                continue
            i = 0
            d_gcol, i = _decode_vlq(seg, i)
            d_src, i = _decode_vlq(seg, i)
            d_sline, i = _decode_vlq(seg, i)
            d_scol, i = _decode_vlq(seg, i)
            gen_col += d_gcol
            src_idx += d_src
            src_line += d_sline
            src_col += d_scol
            out.append((gen_line, gen_col, src_idx, src_line, src_col))
    return out


def test_encode_vlq_known_values():
    assert encode_vlq(0) == "A"
    assert encode_vlq(1) == "C"
    assert encode_vlq(-1) == "D"
    assert encode_vlq(16) == "gB"


def test_encode_vlq_roundtrip():
    for v in (0, 1, -1, 16, -16, 63, 64, -64, 1234, -1234, 100000):
        s = encode_vlq(v)
        decoded, consumed = _decode_vlq(s, 0)
        assert decoded == v
        assert consumed == len(s)


def test_build_source_map_metadata():
    unit = compile_source("x = 1;\ny = x + 1;\n", "t.m")
    sm = build_source_map(unit)
    assert sm["version"] == 3
    assert sm["sources"] == ["t.m"]
    assert sm["sourcesContent"] == ["x = 1;\ny = x + 1;\n"]
    assert sm["names"] == []


def test_build_source_map_maps_each_statement():
    src = "x = 1;\ny = x + 1;\nz = x + y;\n"
    unit = compile_source(src, "t.m")
    sm = build_source_map(unit)
    decoded = _decode_mappings(sm["mappings"])
    src_lines = {src_line + 1 for *_ , src_line, _ in decoded}
    # All three statements must appear as source lines.
    assert {1, 2, 3} <= src_lines


def test_source_map_json_is_valid():
    unit = compile_source("a = 2 + 3;\n", "t.m")
    data = json.loads(unit.source_map_json())
    assert data["version"] == 3
    assert data["sources"] == ["t.m"]
