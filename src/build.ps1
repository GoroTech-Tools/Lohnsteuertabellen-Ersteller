# build.ps1 — Führt den EXE-/ZIP-Build für Lohnsteuertabellen-Ersteller aus
#
# Standardablauf:
#   1) optional Setup prüfen/ausführen (.venv + requirements)
#   2) Build via src\build_exe.py starten
#
# Aufruf:
#   .\src\build.ps1
#   .\src\build.ps1 -SkipSetup
param(
    [switch]$SkipSetup
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$repo = Split-Path $projectRoot -Leaf

# Immer im Projektroot arbeiten
Set-Location $projectRoot

$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$setupScript = Join-Path $PSScriptRoot "setup.ps1"
$buildScript = Join-Path $PSScriptRoot "build_exe.py"

if (-not (Test-Path $buildScript)) {
    throw "Build-Skript nicht gefunden: $buildScript"
}

if (-not $SkipSetup) {
    if (-not (Test-Path $venvPython)) {
        if (-not (Test-Path $setupScript)) {
            throw "Weder .venv noch src\\setup.ps1 gefunden. Erwartet: $venvPython und/oder $setupScript"
        }

        Write-Host "[$repo] .venv fehlt — führe src\\setup.ps1 aus ..."
        & $setupScript
        if ($LASTEXITCODE -ne 0) {
            throw "src\\setup.ps1 fehlgeschlagen (Exit-Code $LASTEXITCODE)."
        }
    }
}

if (-not (Test-Path $venvPython)) {
    throw "Python aus .venv nicht gefunden: $venvPython`nTipp: zuerst .\\src\\setup.ps1 ausführen oder src\\build.ps1 ohne -SkipSetup starten."
}

Write-Host "[$repo] Starte Build über src\build_exe.py ..."
& $venvPython $buildScript

if ($LASTEXITCODE -ne 0) {
    throw "Build fehlgeschlagen (Exit-Code $LASTEXITCODE)."
}

Write-Host "[$repo] Build erfolgreich abgeschlossen." -ForegroundColor Green
