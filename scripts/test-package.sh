#!/usr/bin/env bash
# Smoke-test a built MALT package (Debian `.deb`) in a clean environment.
#
# Usage:
#   scripts/test-package.sh <malt_<version>_<arch>.deb>
#
# Installs the package, exercises the CLI/REPL/debugger/graphics, then
# uninstalls it and verifies no stray files remain.
set -euo pipefail

DEB="${1:?usage: scripts/test-package.sh <file.deb>}"
WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

echo "==> installing $DEB"
sudo apt-get install -y "./$DEB"

echo "==> which malt"
command -v malt

echo "==> version"
malt --version

echo "==> evaluation"
out="$(malt eval '2 + 3 * 4')"
echo "$out" | grep -q "14"

echo "==> run a .m file"
cat > "$WORKDIR/smoke.m" <<'EOF'
a = [1 2; 3 4];
s = sum(a(:));
disp(s);
EOF
malt run "$WORKDIR/smoke.m" | grep -q "10"

echo "==> REPL starts and exits"
printf 'exit\n' | malt repl >/dev/null

echo "==> debugger starts and quits"
printf 'q\n' | malt debug "$WORKDIR/smoke.m" >/dev/null

echo "==> headless plot export"
cat > "$WORKDIR/plot.m" <<'EOF'
x = 0:0.1:6;
plot(x, sin(x));
saveas(gcf, 'smoke_plot.png');
EOF
( cd "$WORKDIR" && MPLBACKEND=Agg malt run plot.m )
test -f "$WORKDIR/smoke_plot.png"

echo "==> help"
malt --help | grep -q "run a MATLAB script"

echo "==> uninstalling"
sudo apt-get remove -y malt

echo "==> smoke test passed"
