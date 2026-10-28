#!/usr/bin/env bash
# Record benchmark results (median + IQR + sample count) for the current
# checkout, tagged with the version and environment metadata.
#
# Usage:
#   scripts/benchmark-record.sh [--full]
#
# Output is appended to benchmarks/results/<version>.txt.
set -euo pipefail

cd "$(dirname "$0")/.."

FULL=0
[ "${1:-}" = "--full" ] && FULL=1

VERSION="$(git describe --tags --always 2>/dev/null || echo unknown)"
OUT="benchmarks/results/${VERSION}.txt"

ENV=$(nix develop -c python - <<'PY'
import platform, sys
import numpy, scipy, matplotlib
print(f"python={sys.version.split()[0]} platform={platform.platform()}")
print(f"numpy={numpy.__version__} scipy={scipy.__version__} matplotlib={matplotlib.__version__}")
PY
)

{
  echo "# MALT benchmark — $VERSION — $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "# $ENV"
  echo
  if [ "$FULL" = "1" ]; then
    nix develop -c python benchmarks/run.py
  else
    nix develop -c python benchmarks/run.py --quick
  fi
} | tee "$OUT"

echo
echo "recorded to $OUT"
