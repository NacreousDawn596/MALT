#!/usr/bin/env bash
# Run the full MALT test suite under the Nix development shell.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> ruff"
nix develop -c ruff check src/malt tests

echo "==> mypy"
nix develop -c mypy src/malt

echo "==> pytest"
nix develop -c pytest "$@"
