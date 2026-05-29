# setup.ps1 — Kompatibilitäts-Wrapper (delegiert an src\setup.ps1)

[CmdletBinding()]
param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "src\setup.ps1"
if (-not (Test-Path $scriptPath)) {
    throw "src\setup.ps1 nicht gefunden: $scriptPath"
}

& $scriptPath @PSBoundParameters
exit $LASTEXITCODE
