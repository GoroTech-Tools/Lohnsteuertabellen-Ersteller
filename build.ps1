# build.ps1 — Führt den EXE-/ZIP-Build für Lohnsteuertabellen-Ersteller aus
#
# Standardablauf:
#   1) optional Setup prüfen/ausführen (.venv + requirements)
#   2) Build via src\build_exe.py starten
#
# Aufruf:
#   .\build.ps1
#   .\build.ps1 -SkipSetup
param(
    [switch]$SkipSetup
)

$ErrorActionPreference = "Stop"
$repo = Split-Path $PSScriptRoot -Leaf

# Immer im Projektroot arbeiten
Set-Location $PSScriptRoot

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$setupScript = Join-Path $PSScriptRoot "setup.ps1"
$buildScript = Join-Path $PSScriptRoot "src\build_exe.py"

if (-not (Test-Path $buildScript)) {
    throw "Build-Skript nicht gefunden: $buildScript"
}

if (-not $SkipSetup) {
    if (-not (Test-Path $venvPython)) {
        if (-not (Test-Path $setupScript)) {
            throw "Weder .venv noch setup.ps1 gefunden. Erwartet: $venvPython und/oder $setupScript"
        }

        Write-Host "[$repo] .venv fehlt — führe setup.ps1 aus ..."
        & $setupScript
        if ($LASTEXITCODE -ne 0) {
            throw "setup.ps1 fehlgeschlagen (Exit-Code $LASTEXITCODE)."
        }
    }
}

if (-not (Test-Path $venvPython)) {
    throw "Python aus .venv nicht gefunden: $venvPython`nTipp: zuerst .\setup.ps1 ausführen oder build.ps1 ohne -SkipSetup starten."
}

Write-Host "[$repo] Starte Build über src\build_exe.py ..."
& $venvPython $buildScript

if ($LASTEXITCODE -ne 0) {
    throw "Build fehlgeschlagen (Exit-Code $LASTEXITCODE)."
}

Write-Host "[$repo] Build erfolgreich abgeschlossen." -ForegroundColor Green
