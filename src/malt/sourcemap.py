"""Source maps: map generated Python back to MATLAB source.

Emits a V3 ("source map revision 3") JSON map — the same format used by
browsers, Node, and debuggers — so that tools can translate a position in the
generated CPython source to the corresponding MATLAB line/column.

The mapping is line-granular: each generated line maps to the most recent
MATLAB source location recorded by the code generator. Column information on
the MATLAB side is preserved (1-based locations are converted to the 0-based
indices the V3 format requires).
"""

from __future__ import annotations

import json
from typing import Any

_BASE64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"


def encode_vlq(value: int) -> str:
    """Base64 VLQ-encode a signed integer (source-map segment encoding)."""
    vlq = (value << 1) if value >= 0 else ((-value) << 1) | 1
    out = ""
    while True:
        digit = vlq & 31
        vlq >>= 5
        if vlq > 0:
            digit |= 32
        out += _BASE64[digit]
        if vlq == 0:
            return out


def _decode_vlq(s: str) -> tuple[list[int], int]:
    """Decode base64 VLQ from the start of ``s``; return (values, consumed)."""
    values: list[int] = []
    shift = 0
    value = 0
    i = 0
    while i < len(s):
        digit = _BASE64.index(s[i])
        i += 1
        value |= (digit & 31) << shift
        if digit & 32:
            shift += 5
            continue
        # sign bit
        values.append((value >> 1) if (value & 1) == 0 else -(value >> 1))
        value = 0
        shift = 0
        if i >= len(s) or s[i] == "," or s[i] == ";":
            return values, i
    return values, i


def _per_line_mappings(unit: Any) -> list[tuple[int, int, int]]:
    """Return ``(generated_line, src_line, src_col)`` (1-based src) per line."""
    lines = unit.generated_source.split("\n")
    mapping = unit.source_map
    result: list[tuple[int, int, int]] = []
    mi = 0
    n = len(mapping)
    for gen_line in range(1, len(lines) + 1):
        while mi + 1 < n and mapping[mi + 1][0] <= gen_line:
            mi += 1
        if mi < n:
            loc = mapping[mi][1]
            result.append((gen_line, loc.line, loc.column))
    return result


def build_source_map(unit: Any) -> dict[str, Any]:
    """Build a V3 source-map dictionary for a compiled unit."""
    segments = _per_line_mappings(unit)
    out: list[str] = []
    prev_src_line = 0
    prev_src_col = 0
    for _, src_line, src_col in segments:
        seg = encode_vlq(0)  # generated column (line start)
        seg += encode_vlq(0)  # source index (always 0)
        seg += encode_vlq((src_line - 1) - prev_src_line)
        seg += encode_vlq((src_col - 1) - prev_src_col)
        out.append(seg)
        prev_src_line = src_line - 1
        prev_src_col = src_col - 1
    return {
        "version": 3,
        "file": f"<malt-generated:{unit.filename}>",
        "sourceRoot": "",
        "sources": [unit.filename],
        "sourcesContent": [unit.source],
        "names": [],
        "mappings": ";".join(out),
    }


def build_source_map_json(unit: Any) -> str:
    """Return the V3 source map as an indented JSON string."""
    return json.dumps(build_source_map(unit), indent=2)
