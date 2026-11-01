param([int]$Port = 8765)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$venvPython = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
$basePython = $null
$candidates = @()
if (Get-Command py -ErrorAction SilentlyContinue) {
    try {
        $resolved = & py -3 -c 'import sys; print(sys.executable)' 2>$null
        if ($LASTEXITCODE -eq 0) { $candidates += $resolved }
    } catch { $resolved = $null }
}
$candidates += (Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe')
if (Get-Command python -ErrorAction SilentlyContinue) {
    $candidates += (Get-Command python).Source
}
foreach ($candidate in $candidates) {
    if ((Test-Path -LiteralPath $candidate) -and ($candidate -notlike '*WindowsApps*')) {
        try {
            & $candidate -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>$null
            if ($LASTEXITCODE -eq 0) { $basePython = $candidate; break }
        } catch { continue }
    }
}
if (-not (Test-Path -LiteralPath $venvPython)) {
    if (-not $basePython) { throw 'Python 3.10+ is required. Install Python with pip, then run again.' }
    & $basePython -m venv --without-pip (Join-Path $PSScriptRoot '.venv')
    # Some embedded Python distributions cannot bootstrap pip; base pip can target the venv.
    if (-not (Test-Path -LiteralPath $venvPython)) { throw 'Could not create the Python environment.' }
}
try {
    & $venvPython -c 'import sys; sys.path.insert(0,"web/.deps"); import fastapi, uvicorn, multipart, pypdf, pymupdf' 2>$null
    $dependenciesReady = ($LASTEXITCODE -eq 0)
} catch { $dependenciesReady = $false }
if (-not $dependenciesReady) {
    try {
        & $venvPython -m pip --version 2>$null
        $hasPip = ($LASTEXITCODE -eq 0)
    } catch { $hasPip = $false }
    if ($hasPip) {
        & $venvPython -m pip install -r (Join-Path $PSScriptRoot 'requirements.lock.txt')
    } elseif ($basePython) {
        & $basePython -m pip --python $venvPython install -r (Join-Path $PSScriptRoot 'requirements.lock.txt')
    } else { throw 'Dependencies are missing. Install pip for this environment and retry.' }
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed. Check the network and retry.' }
}
Write-Host ''
Write-Host "Tree Court: http://127.0.0.1:$Port" -ForegroundColor Green
Write-Host 'Keep this window open. Press Ctrl+C to stop. Data: data/runtime/'
& $venvPython -m uvicorn web.backend.app:app --host 127.0.0.1 --port $Port
exit $LASTEXITCODE
