# Get the directory where the script is located
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Locate a Python venv
$PythonExe = $null

if ($env:VIRTUAL_ENV) {
    Write-Host "Using active virtual environment: $env:VIRTUAL_ENV" -ForegroundColor Yellow
    $PythonExe = Join-Path $env:VIRTUAL_ENV "Scripts\python.exe"
} elseif (Test-Path (Join-Path $ScriptDir "venv\Scripts\python.exe")) {
    Write-Host "Using venv (local)..." -ForegroundColor Yellow
    $PythonExe = Join-Path $ScriptDir "venv\Scripts\python.exe"
} elseif (Test-Path (Join-Path $ScriptDir ".venv\Scripts\python.exe")) {
    Write-Host "Using .venv (local)..." -ForegroundColor Yellow
    $PythonExe = Join-Path $ScriptDir ".venv\Scripts\python.exe"
} elseif (Test-Path (Join-Path $ScriptDir "..\venv\Scripts\python.exe")) {
    Write-Host "Using venv (parent)..." -ForegroundColor Yellow
    $PythonExe = Join-Path $ScriptDir "..\venv\Scripts\python.exe"
} elseif (Test-Path (Join-Path $ScriptDir "..\.venv\Scripts\python.exe")) {
    Write-Host "Using .venv (parent)..." -ForegroundColor Yellow
    $PythonExe = Join-Path $ScriptDir "..\.venv\Scripts\python.exe"
} else {
    Write-Host "Warning: No virtual environment found (venv or .venv)." -ForegroundColor Red
    Write-Host "Attempting to use system python..." -ForegroundColor Yellow
    $PythonExe = "python"
}

# Verify pip is available
try {
    & $PythonExe -m pip --version | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "pip not found" }
} catch {
    Write-Host "Error: pip command not found." -ForegroundColor Red
    Write-Host "Please ensure python and pip are installed and you are in a virtual environment."
    exit 1
}

Write-Host "Cleaning up previous installation..." -ForegroundColor Yellow

# Uninstall existing package
& $PythonExe -m pip uninstall -y ontobdc-view

# Clean build artifacts
Write-Host "Removing build artifacts..." -ForegroundColor Yellow
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue (Join-Path $ScriptDir "build")
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue (Join-Path $ScriptDir "dist")
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue (Join-Path $ScriptDir "src\ontobdc_view.egg-info")
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue (Join-Path $ScriptDir "src\ontobdc_view\__pycache__")

Write-Host "Reinstalling in editable mode..." -ForegroundColor Yellow

& $PythonExe -c "import hatchling" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "X Missing build dependency: hatchling" -ForegroundColor Red
    Write-Host "This environment does not have hatchling installed, and pip needs it to install this project." -ForegroundColor Yellow
    Write-Host "If you are offline, pip cannot download build dependencies." -ForegroundColor Yellow
    Write-Host "Fix: pip install `"hatchling>=1.26`"" -ForegroundColor Yellow
    exit 1
}

# hatchling's editable-install hook needs `editables`, which --no-build-isolation
# prevents pip from fetching on its own.
& $PythonExe -c "import editables" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "X Missing build dependency: editables" -ForegroundColor Red
    Write-Host "hatchling needs the 'editables' package to build an editable install, and --no-build-isolation prevents pip from fetching it automatically." -ForegroundColor Yellow
    Write-Host "Fix: pip install editables" -ForegroundColor Yellow
    exit 1
}

& $PythonExe -m pip install -e $ScriptDir --no-build-isolation

if ($LASTEXITCODE -eq 0) {
    Write-Host "Successfully reinstalled ontobdc-view!" -ForegroundColor Green
} else {
    Write-Host "X Installation failed." -ForegroundColor Red
    exit 1
}
