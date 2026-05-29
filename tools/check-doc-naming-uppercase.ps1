param(
    [string]$WorkspaceRoot,
    [switch]$IncludeBackups
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($WorkspaceRoot)) {
    $WorkspaceRoot = Split-Path -Path $PSScriptRoot -Parent
}

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
if ($PSVersionTable.PSVersion.Major -ge 6) {
    $OutputEncoding = [System.Text.Encoding]::UTF8
}

if (-not (Test-Path $WorkspaceRoot)) {
    Write-Host "WorkspaceRoot nicht gefunden: $WorkspaceRoot" -ForegroundColor Red
    exit 2
}

$legacyPatterns = @(
    'docs/Liesmich.txt',
    'docs\\Liesmich.txt',
    'docs/Dokumentation_Anwender.md',
    'docs/Dokumentation_Technik.md',
    'docs/Dokumentation_Checkliste.md'
)

$docExtensions = @('.md', '.txt', '.rst')
$docStemRegex = 'doku|dokumentation|readme|liesmich|anleitung|kurz|contributing|technik|anwender|arbeitsmappe|checkliste|entwickler'
$ignorePathRegex = '\\.venv\\|\\dist\\|\\build\\|\\release\\|\\.git\\|\\node_modules\\'

$projectDirs = Get-ChildItem -Path $WorkspaceRoot -Directory
if (-not $IncludeBackups) {
    $projectDirs = $projectDirs | Where-Object { $_.Name -ne '_Backups' }
}

$violatingNames = @()
$legacyHits = @()

foreach ($project in $projectDirs) {
    $docsDir = Join-Path $project.FullName 'docs'
    if (-not (Test-Path $docsDir)) { continue }

    $docFiles = Get-ChildItem -Path $docsDir -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $docExtensions -contains $_.Extension.ToLowerInvariant() }

    foreach ($file in $docFiles) {
        $stem = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)
        $isDocLike = $stem -match $docStemRegex
        if (-not $isDocLike) { continue }

        if (-not ($stem -ceq $stem.ToUpperInvariant())) {
            $violatingNames += [PSCustomObject]@{
                Project  = $project.Name
                Relative = $file.FullName.Substring($project.FullName.Length + 1)
                Name     = $file.Name
            }
        }
    }

    $textFiles = Get-ChildItem -Path $project.FullName -Recurse -File -Include *.md,*.txt,*.ps1,*.py,*.json,*.yml,*.yaml,*.bat -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -notmatch $ignorePathRegex }

    foreach ($file in $textFiles) {
        $content = Get-Content -Path $file.FullName -Raw -ErrorAction SilentlyContinue
        if ($null -eq $content) { continue }

        foreach ($pattern in $legacyPatterns) {
            if ($content -cmatch [regex]::Escape($pattern)) {
                $legacyHits += [PSCustomObject]@{
                    Project = $project.Name
                    File    = $file.FullName.Substring($project.FullName.Length + 1)
                    Pattern = $pattern
                }
            }
        }
    }
}

$hasIssues = $false

Write-Host "=== DOKU-NAMING CHECK (GROSSBUCHSTABEN) ===" -ForegroundColor Cyan
Write-Host "Workspace: $WorkspaceRoot"
Write-Host "Projekte geprüft: $($projectDirs.Count)"

if ($violatingNames.Count -gt 0) {
    $hasIssues = $true
    Write-Host "`n[FEHLER] Nicht-großgeschriebene Doku-Dateinamen gefunden:" -ForegroundColor Red
    $violatingNames |
        Sort-Object Project, Relative |
        Format-Table -AutoSize | Out-String -Width 240 |
        Write-Host
} else {
    Write-Host "`n[OK] Alle relevanten Doku-Dateinamen sind in GROSSBUCHSTABEN." -ForegroundColor Green
}

if ($legacyHits.Count -gt 0) {
    $hasIssues = $true
    Write-Host "`n[FEHLER] Alte gemischte Doku-Referenzen gefunden:" -ForegroundColor Red
    $legacyHits |
        Sort-Object Project, File, Pattern |
        Format-Table -AutoSize | Out-String -Width 240 |
        Write-Host
} else {
    Write-Host "`n[OK] Keine alten gemischten Doku-Referenzen gefunden." -ForegroundColor Green
}

if ($hasIssues) {
    Write-Host "`nErgebnis: FEHLER" -ForegroundColor Red
    exit 1
}

Write-Host "`nErgebnis: OK" -ForegroundColor Green
exit 0
