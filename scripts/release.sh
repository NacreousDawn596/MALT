#!/usr/bin/env bash
# Release helper: build the package, test it outside the dev shell, and tag.
#
# Usage:
#   scripts/release.sh <version>     e.g. scripts/release.sh 0.2.0
#
# This is a dry-run unless RELEASE_CONFIRM=1 is set (which also tags and prints
# the commands to push). It does NOT publish anything on its own.
set -euo pipefail

cd "$(dirname "$0")/.."

VERSION="${1:?usage: scripts/release.sh <version>}"
CONFIRM="${RELEASE_CONFIRM:-0}"

echo "==> verifying a clean checkout is up to date"
git diff --quiet || { echo "working tree is dirty; commit or stash first" >&2; exit 1; }

echo "==> running the full test suite"
MALT_REQUIRE_OCTAVE=1 nix develop -c pytest -q

echo "==> lint and type checks"
nix develop -c ruff check .
nix develop -c mypy src/malt

echo "==> nix flake check"
nix flake check

echo "==> building the release package"
nix build .#default

echo "==> smoke-testing the built CLI outside the dev shell"
./result/bin/malt --version
./result/bin/malt eval "2 + 3 * 4"
./result/bin/malt run examples/basics/hello.m

echo "==> release build verified ($VERSION)"
if [ "$CONFIRM" = "1" ]; then
    git tag "v$VERSION"
    echo "tagged v$VERSION — push with: git push origin v$VERSION"
else
    echo "dry run. set RELEASE_CONFIRM=1 to create the v$VERSION tag."
fi
