# setup.ps1 — Erstellt .venv und installiert Abhängigkeiten aus requirements.txt
# Aufruf: .\setup.ps1
# Optional: .\setup.ps1 -Force  (löscht bestehende .venv und erstellt neu)
param([switch]$Force)

$ErrorActionPreference = "Stop"
$repo = Split-Path $PSScriptRoot -Leaf

if ($Force -and (Test-Path ".\.venv")) {
    Write-Host "[$repo] Entferne bestehende .venv ..."
    Remove-Item ".\.venv" -Recurse -Force
}

if (-not (Test-Path ".\.venv")) {
    Write-Host "[$repo] Erstelle .venv ..."
    python -m venv .venv
} else {
    Write-Host "[$repo] .venv bereits vorhanden."
}

Write-Host "[$repo] Aktualisiere pip ..."
.\.venv\Scripts\python.exe -m pip install --upgrade pip -q

if (Test-Path ".\requirements.txt") {
    Write-Host "[$repo] Installiere Pakete aus requirements.txt ..."
    .\.venv\Scripts\python.exe -m pip install -r requirements.txt -q
    Write-Host "[$repo] Fertig. Aktivieren mit: .\.venv\Scripts\Activate.ps1"
} else {
    Write-Host "[$repo] Keine requirements.txt gefunden — .venv angelegt, aber leer."
}
