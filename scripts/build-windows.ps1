
#Requires -Version 5.1

<#
.SYNOPSIS
    Build the MALT Windows CLI, Qt6 GUI and per-user installer.

.DESCRIPTION
    Creates an isolated Python environment, installs the Qt6-only build
    dependencies, validates the runtime, builds two independent PyInstaller
    one-file executables, and packages them with Inno Setup.

.OUTPUTS
    dist/malt.exe
    dist/malt-gui.exe
    dist/MALT-Setup-<version>-x64.exe

.REQUIREMENTS
    Windows x64
    Python 3.11+
    Inno Setup 6
    PyQt6 only (no PyQt5 / PySide2 / PySide6)
#>

[CmdletBinding()]
param(
    [string]$Version = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

function Write-Section {
    param([string]$Message)

    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Invoke-Native {
    param(
        [Parameter(Mandatory)]
        [string]$FilePath,

        [Parameter(Mandatory)]
        [string[]]$Arguments,

        [Parameter(Mandatory)]
        [string]$Label
    )

    Write-Section $Label

    & $FilePath @Arguments

    $exitCode = $LASTEXITCODE

    if ($exitCode -ne 0) {
        throw "$Label failed with exit code $exitCode."
    }
}

function Assert-File {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Required file does not exist: $Path"
    }
}

function Assert-Artifact {
    param(
        [string]$Path,
        [string]$Description
    )

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "$Description was not produced: $Path"
    }

    $item = Get-Item -LiteralPath $Path

    if ($item.Length -le 0) {
        throw "$Description is empty: $Path"
    }

    Write-Host ("  OK  {0} ({1:N2} MB)" -f $Path, ($item.Length / 1MB)) `
        -ForegroundColor Green
}

# ---------------------------------------------------------------------------
# Repository paths
# ---------------------------------------------------------------------------

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repoRoot

$initFile = Join-Path $repoRoot "src\malt\__init__.py"
$projectFile = Join-Path $repoRoot "pyproject.toml"
$requirementsFile = Join-Path $repoRoot "packaging\windows\requirements-build.txt"

$cliEntry = Join-Path $repoRoot "packaging\entrypoints\malt_cli.py"
$guiEntry = Join-Path $repoRoot "packaging\entrypoints\malt_gui.py"
$installerScript = Join-Path $repoRoot "packaging\windows\malt-installer.iss"
$iconFile = Join-Path $repoRoot "packaging\icons\malt.ico"

$distDir = Join-Path $repoRoot "dist"
$buildDir = Join-Path $repoRoot "build\windows"
$specDir = Join-Path $buildDir "specs"

$venvDir = Join-Path $repoRoot ".venv-windows"
$venvPython = Join-Path $venvDir "Scripts\python.exe"

$cliExe = Join-Path $distDir "malt.exe"
$guiExe = Join-Path $distDir "malt-gui.exe"

# ---------------------------------------------------------------------------
# Validate source files
# ---------------------------------------------------------------------------

Write-Section "Validating repository"

@(
    $initFile,
    $projectFile,
    $requirementsFile,
    $cliEntry,
    $guiEntry,
    $installerScript,
    $iconFile
) | ForEach-Object {
    Assert-File $_
}

# ---------------------------------------------------------------------------
# Resolve and validate version
# ---------------------------------------------------------------------------

if ([string]::IsNullOrWhiteSpace($Version)) {
    $initContent = Get-Content -LiteralPath $initFile -Raw

    $versionMatch = [regex]::Match(
        $initContent,
        '__version__\s*=\s*["'']([^"'']+)["'']'
    )

    if (-not $versionMatch.Success) {
        throw "Could not extract MALT version from src/malt/__init__.py"
    }

    $Version = $versionMatch.Groups[1].Value
}

if ($Version -notmatch '^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$') {
    throw "Invalid version format: $Version"
}

$projectContent = Get-Content -LiteralPath $projectFile -Raw
$projectVersion = [regex]::Match(
    $projectContent,
    '(?m)^\s*version\s*=\s*["'']([^"'']+)["'']'
)

if (-not $projectVersion.Success) {
    throw "Could not extract version from pyproject.toml"
}

if ($projectVersion.Groups[1].Value -ne $Version) {
    throw "Version mismatch: package=$($projectVersion.Groups[1].Value), source=$Version"
}

Write-Host "MALT version: $Version" -ForegroundColor Green
Write-Host "Repository:   $repoRoot"

# ---------------------------------------------------------------------------
# Validate the build requirements before creating the environment
# ---------------------------------------------------------------------------

Write-Section "Checking Qt dependency configuration"

$requirementsContent = Get-Content -LiteralPath $requirementsFile -Raw

$conflictingQt = [regex]::Match(
    $requirementsContent,
    '(?im)^\s*(PyQt5|PySide2|PySide6)(?:[-_.][A-Za-z0-9_.-]+)?(?:\s*[<=>!~].*)?$'
)

if ($conflictingQt.Success) {
    throw @"
Incompatible Qt binding found in requirements-build.txt:

    $($conflictingQt.Value.Trim())

MALT Windows packaging must use PyQt6 only.
Remove PyQt5, PySide2 and PySide6 from packaging/windows/requirements-build.txt.
"@
}

if ($requirementsContent -notmatch '(?im)^\s*PyQt6(?:\s|[<=>!~]|$)') {
    throw "PyQt6 is missing from packaging/windows/requirements-build.txt"
}

Write-Host "Qt dependency configuration: OK" -ForegroundColor Green

# ---------------------------------------------------------------------------
# Find Python
# ---------------------------------------------------------------------------

Write-Section "Locating Python"

$pythonCommand = Get-Command python -ErrorAction Stop

if ($pythonCommand.CommandType -ne "Application") {
    throw "The 'python' command must resolve to a Python executable."
}

$pythonExe = $pythonCommand.Source

Invoke-Native `
    -FilePath $pythonExe `
    -Arguments @("-c", "import sys; print(sys.version); raise SystemExit(0 if sys.version_info >= (3, 11) else 1)") `
    -Label "Checking Python version (3.11+)"

# ---------------------------------------------------------------------------
# Create a completely isolated build environment
# ---------------------------------------------------------------------------

Write-Section "Creating clean build environment"

if (Test-Path -LiteralPath $venvDir) {
    Write-Host "Removing previous build environment..."
    Remove-Item -LiteralPath $venvDir -Recurse -Force
}

Invoke-Native `
    -FilePath $pythonExe `
    -Arguments @("-m", "venv", $venvDir) `
    -Label "Creating virtual environment"

if (-not (Test-Path -LiteralPath $venvPython)) {
    throw "Virtual environment Python was not created."
}

# ---------------------------------------------------------------------------
# Install dependencies
# ---------------------------------------------------------------------------

Write-Section "Installing build dependencies"

Invoke-Native `
    -FilePath $venvPython `
    -Arguments @("-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel") `
    -Label "Upgrading build tooling"

Invoke-Native `
    -FilePath $venvPython `
    -Arguments @("-m", "pip", "install", "-r", $requirementsFile) `
    -Label "Installing Qt6-only requirements"

Invoke-Native `
    -FilePath $venvPython `
    -Arguments @("-m", "pip", "install", "--no-deps", "-e", $repoRoot) `
    -Label "Installing MALT"

Invoke-Native `
    -FilePath $venvPython `
    -Arguments @("-m", "pip", "check") `
    -Label "Checking Python dependencies"

# ---------------------------------------------------------------------------
# Qt6 preflight
# ---------------------------------------------------------------------------

Write-Section "Validating PyQt6 and Matplotlib"

$oldQtApi = $env:QT_API
$oldMplBackend = $env:MPLBACKEND

$env:QT_API = "PyQt6"
$env:MPLBACKEND = "QtAgg"

$preflightCode = @'
import importlib.util

conflicts = ("PyQt5", "PySide2", "PySide6")
installed = [name for name in conflicts if importlib.util.find_spec(name)]

if installed:
    raise SystemExit(f"Conflicting Qt bindings found: {installed}")

import PyQt6
from PyQt6 import QtCore

import numpy
import scipy
import matplotlib

matplotlib.use("QtAgg", force=True)

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from scipy import integrate, optimize
from scipy.linalg import lu

print("PyQt6:", QtCore.QT_VERSION_STR)
print("NumPy:", numpy.__version__)
print("SciPy:", scipy.__version__)
print("Matplotlib:", matplotlib.__version__)
print("Matplotlib backend:", matplotlib.get_backend())
print("Qt binding validation passed.")
'@

Invoke-Native `
    -FilePath $venvPython `
    -Arguments @("-c", $preflightCode) `
    -Label "Testing Qt6 runtime dependencies"

# ---------------------------------------------------------------------------
# Prepare clean output directories
# ---------------------------------------------------------------------------

Write-Section "Preparing build directories"

if (-not (Test-Path -LiteralPath $distDir)) {
    New-Item -ItemType Directory -Path $distDir -Force | Out-Null
}

if (Test-Path -LiteralPath $buildDir) {
    Remove-Item -LiteralPath $buildDir -Recurse -Force
}

New-Item -ItemType Directory -Path $specDir -Force | Out-Null

# Remove stale artifacts from previous builds.
@(
    $cliExe,
    $guiExe,
    (Join-Path $distDir "MALT-Setup-$Version-x64.exe")
) | ForEach-Object {
    if (Test-Path -LiteralPath $_) {
        Remove-Item -LiteralPath $_ -Force
    }
}

# ---------------------------------------------------------------------------
# Generate a Qt6 runtime hook
# ---------------------------------------------------------------------------

Write-Section "Generating Qt6 runtime hook"

$runtimeHook = Join-Path $buildDir "rthook_qt6.py"

$runtimeHookContent = @'
"""
MALT PyInstaller runtime hook.

Executed before importing the MALT application.
Force the bundled Qt binding to PyQt6 and default Matplotlib to QtAgg.
Respect an explicitly requested backend such as MPLBACKEND=Agg.
"""

import os

os.environ["QT_API"] = "PyQt6"
os.environ.setdefault("MPLBACKEND", "QtAgg")
'@

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)

[System.IO.File]::WriteAllText(
    $runtimeHook,
    $runtimeHookContent,
    $utf8NoBom
)

# ---------------------------------------------------------------------------
# Shared PyInstaller configuration
# ---------------------------------------------------------------------------

$commonArguments = @(
    "--noconfirm",
    "--clean",
    "--onefile",

    "--paths", "src",

    "--distpath", $distDir,
    "--specpath", $specDir,

    "--runtime-hook", $runtimeHook,

    # Qt6: collect its Python package and native Qt resources.
    "--collect-all", "PyQt6",

    # Matplotlib data: fonts, styles and other runtime resources.
    # Avoid --collect-all matplotlib: that pulls in unrelated backends,
    # testing modules, optional GUI frameworks and unnecessary dependencies.
    "--collect-data", "matplotlib",

    # NumPy/SciPy native libraries. Their PyInstaller hooks handle modules.
    "--collect-binaries", "numpy",
    "--collect-binaries", "scipy",

    # Explicit runtime backends.
    "--hidden-import", "matplotlib.backends.backend_qtagg",
    "--hidden-import", "matplotlib.backends.backend_agg",
    "--hidden-import", "matplotlib.backends.qt_compat",
    "--hidden-import", "matplotlib.backends.backend_pdf",
    "--hidden-import", "matplotlib.backends.backend_svg",

    # MALT's SciPy runtime functionality.
    "--hidden-import", "scipy.integrate",
    "--hidden-import", "scipy.optimize",
    "--hidden-import", "scipy.linalg",

    # Never allow another Qt binding into this frozen application.
    "--exclude-module", "PyQt5",
    "--exclude-module", "PySide2",
    "--exclude-module", "PySide6"
)

# ---------------------------------------------------------------------------
# Build CLI executable
# ---------------------------------------------------------------------------

Write-Section "Building MALT CLI"

$cliArguments = @($commonArguments) + @(
    "--workpath", (Join-Path $buildDir "cli"),
    "--name", "malt",
    "--console",
    $cliEntry
)

Invoke-Native `
    -FilePath $venvPython `
    -Arguments (@("-m", "PyInstaller") + $cliArguments) `
    -Label "PyInstaller: CLI"

Assert-Artifact -Path $cliExe -Description "MALT CLI executable"

# ---------------------------------------------------------------------------
# Build GUI executable
# ---------------------------------------------------------------------------

Write-Section "Building MALT Qt6 GUI"

$guiArguments = @($commonArguments) + @(
    "--workpath", (Join-Path $buildDir "gui"),
    "--name", "malt-gui",
    "--windowed",
    $guiEntry
)

Invoke-Native `
    -FilePath $venvPython `
    -Arguments (@("-m", "PyInstaller") + $guiArguments) `
    -Label "PyInstaller: GUI"

Assert-Artifact -Path $guiExe -Description "MALT GUI executable"

# Restore the build machine's original environment.
if ($null -eq $oldQtApi) {
    Remove-Item Env:QT_API -ErrorAction SilentlyContinue
}
else {
    $env:QT_API = $oldQtApi
}

if ($null -eq $oldMplBackend) {
    Remove-Item Env:MPLBACKEND -ErrorAction SilentlyContinue
}
else {
    $env:MPLBACKEND = $oldMplBackend
}

# ---------------------------------------------------------------------------
# Locate Inno Setup
# ---------------------------------------------------------------------------

Write-Section "Locating Inno Setup 6"

$isccCandidates = @(
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe"
)

$iscc = $isccCandidates |
    Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } |
    Select-Object -First 1

if (-not $iscc) {
    $isccCommand = Get-Command ISCC.exe -ErrorAction SilentlyContinue

    if ($isccCommand) {
        $iscc = $isccCommand.Source
    }
}

if (-not $iscc) {
    throw @"
Inno Setup 6 was not found.

Install it using:
    choco install innosetup --no-progress -y
"@
}

Write-Host "Using: $iscc"

# ---------------------------------------------------------------------------
# Build installer
# ---------------------------------------------------------------------------

Write-Section "Building MALT installer"

Invoke-Native `
    -FilePath $iscc `
    -Arguments @(
        "/DAppVersion=$Version",
        $installerScript
    ) `
    -Label "Inno Setup"

$installer = Join-Path $distDir "MALT-Setup-$Version-x64.exe"

Assert-Artifact `
    -Path $installer `
    -Description "MALT Windows installer"

# ---------------------------------------------------------------------------
# Final artifact report
# ---------------------------------------------------------------------------

Write-Section "Build completed successfully"

Write-Host ""
Write-Host "MALT $Version — Windows x64" -ForegroundColor Green
Write-Host ""

Write-Host "CLI:"
Write-Host "  $cliExe"

Write-Host ""
Write-Host "GUI:"
Write-Host "  $guiExe"

Write-Host ""
Write-Host "Installer:"
Write-Host "  $installer"

Write-Host ""
Write-Host "All three artifacts were produced." -ForegroundColor Green
