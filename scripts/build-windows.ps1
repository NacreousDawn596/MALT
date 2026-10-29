# Build the MALT Windows executable(s) and installer.
#
# Usage (on a Windows x64 runner, from the repo root):
#   powershell -ExecutionPolicy Bypass -File scripts\build-windows.ps1
#
# Requires Python 3.11+, and Inno Setup 6 installed at the default location.
# Produces:
#   dist\malt.exe              (console CLI)
#   dist\malt-gui.exe          (windowed GUI)
#   dist\MALT-Setup-<version>-x64.exe
param(
    [string]$Version = ""
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

if (-not $Version) {
    $Version = (Select-String -Path "src\malt\__init__.py" `
        -Pattern '__version__ = "([^"]+)"').Matches[0].Groups[1].Value
}
Write-Host "==> building MALT $Version (x64)"

Write-Host "==> installing build dependencies"
python -m pip install --upgrade pip setuptools wheel
python -m pip install numpy scipy matplotlib pyqt6 pyinstaller

Write-Host "==> building CLI executable (malt.exe)"
python -m PyInstaller --noconfirm --clean --onefile --name malt `
    --collect-all numpy --collect-all scipy --collect-all matplotlib `
    --collect-all PyQt6 --icon packaging\icons\malt.ico `
    packaging\entrypoints\malt_cli.py

Write-Host "==> building GUI executable (malt-gui.exe)"
python -m PyInstaller --noconfirm --clean --onefile --windowed --name malt-gui `
    --collect-all numpy --collect-all scipy --collect-all matplotlib `
    --collect-all PyQt6 --icon packaging\icons\malt.ico `
    packaging\entrypoints\malt_gui.py

if (-not (Test-Path "dist\malt.exe")) { throw "malt.exe was not produced" }
if (-not (Test-Path "dist\malt-gui.exe")) { throw "malt-gui.exe was not produced" }

Write-Host "==> building installer with Inno Setup"
$iscc = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if (-not (Test-Path $iscc)) {
    $iscc = "C:\Program Files\Inno Setup 6\ISCC.exe"
}
if (-not (Test-Path $iscc)) { throw "Inno Setup 6 not found" }

& $iscc "/DAppVersion=$Version" packaging\windows\malt-installer.iss
if ($LASTEXITCODE -ne 0) { throw "Inno Setup failed" }

$installer = "dist\MALT-Setup-$Version-x64.exe"
if (-not (Test-Path $installer)) { throw "installer was not produced" }

Write-Host "==> artifacts:"
Write-Host "  $((Resolve-Path 'dist\malt.exe').Path)"
Write-Host "  $((Resolve-Path 'dist\malt-gui.exe').Path)"
Write-Host "  $((Resolve-Path $installer).Path)"
