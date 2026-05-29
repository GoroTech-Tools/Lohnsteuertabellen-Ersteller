# build.ps1 — Kompatibilitäts-Wrapper (delegiert an src\build.ps1)

[CmdletBinding()]
param(
    [switch]$SkipSetup
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "src\build.ps1"
if (-not (Test-Path $scriptPath)) {
    throw "src\build.ps1 nicht gefunden: $scriptPath"
}

& $scriptPath @PSBoundParameters
exit $LASTEXITCODE
