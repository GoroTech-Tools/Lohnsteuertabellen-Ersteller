# setup.ps1 — NUR Setup: Erstellt .venv und installiert Abhängigkeiten aus src\requirements.txt
# Aufruf: .\src\setup.ps1
# Optional: .\src\setup.ps1 -Force  (löscht bestehende .venv und erstellt neu)
param([switch]$Force)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $projectRoot
$repo = Split-Path $projectRoot -Leaf
$requirementsFile = Join-Path $PSScriptRoot "requirements.txt"

# Python-Interpreter ermitteln (python oder py -3)
$pythonCmd = $null

if (Get-Command python -ErrorAction SilentlyContinue) {
    try {
        & python -V *> $null
        if ($LASTEXITCODE -eq 0) {
            $pythonCmd = @("python")
        }
    } catch {
        # Ignorieren und auf py -3 prüfen
    }
}

if (-not $pythonCmd -and (Get-Command py -ErrorAction SilentlyContinue)) {
    try {
        & py -3 -V *> $null
        if ($LASTEXITCODE -eq 0) {
            $pythonCmd = @("py", "-3")
        }
    } catch {
        # wird unten abgefangen
    }
}

if (-not $pythonCmd) {
    throw "Weder ein lauffähiges 'python' noch 'py -3' wurde gefunden. Bitte Python installieren oder PATH/App-Ausführungsalias prüfen."
}

if ($Force -and (Test-Path ".\.venv")) {
    Write-Host "[$repo] Entferne bestehende .venv ..."
    Remove-Item ".\.venv" -Recurse -Force
}

if (-not (Test-Path ".\.venv")) {
    Write-Host "[$repo] Erstelle .venv ..."
    if ($pythonCmd.Length -eq 1) {
        & $pythonCmd[0] -m venv .venv
    } else {
        & $pythonCmd[0] $pythonCmd[1] -m venv .venv
    }
} else {
    Write-Host "[$repo] .venv bereits vorhanden."
}

Write-Host "[$repo] Aktualisiere pip ..."
.\.venv\Scripts\python.exe -m pip install --upgrade pip -q

if (Test-Path $requirementsFile) {
    Write-Host "[$repo] Installiere Pakete aus src\requirements.txt ..."
    .\.venv\Scripts\python.exe -m pip install -r $requirementsFile -q
    Write-Host "[$repo] Fertig. Aktivieren mit: .\.venv\Scripts\Activate.ps1"
} else {
    Write-Host "[$repo] Keine src\requirements.txt gefunden — .venv angelegt, aber leer."
}
