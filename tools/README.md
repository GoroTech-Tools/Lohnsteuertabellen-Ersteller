# Tools

Dieses Verzeichnis enthält Hilfsskripte für Qualitätssicherung und Wartung im Repository.

## Enthaltene Skripte

### `check-doc-naming-uppercase.ps1`

Prüft projektübergreifend im Workspace, ob dokumentationsnahe Dateien in `docs/` konsistent in **GROSSBUCHSTABEN** benannt sind und ob veraltete gemischte Doku-Referenzen noch im Code vorkommen.

#### Was wird geprüft?

- Dateinamen unter `docs/` mit Doku-Bezug (z. B. `DOKUMENTATION`, `README`, `LIESMICH`, `ANWENDER`, `TECHNIK`, `CHECKLISTE`) müssen im Stem vollständig großgeschrieben sein.
- Veraltete Referenzmuster wie z. B. `docs/Dokumentation_Anwender.md` oder `docs/Liesmich.txt` werden im Quelltext gesucht.
- Standardmäßig werden übliche Build-/Artefaktordner ignoriert (`.venv`, `dist`, `build`, `release`, `.git`, `node_modules`).

#### Parameter

- `-WorkspaceRoot <Pfad>` (optional): Basisordner mit den zu prüfenden Projekten. Ohne Angabe wird automatisch der Elternordner von `tools/` verwendet.
- `-IncludeBackups` (optional, Switch): Bezieht zusätzlich den Ordner `_Backups` in die Prüfung ein.

#### Beispiele

```powershell
# Standardprüfung mit automatisch erkanntem WorkspaceRoot
.\tools\check-doc-naming-uppercase.ps1

# Expliziter Root-Pfad
.\tools\check-doc-naming-uppercase.ps1 -WorkspaceRoot "D:\OneDrive\Git-Projekte INN-tegrativ gGmbH"

# Inklusive _Backups
.\tools\check-doc-naming-uppercase.ps1 -IncludeBackups
```

#### Exit-Codes

- `0` = OK, keine Verstöße gefunden
- `1` = Verstöße gegen Namens-/Referenzregeln gefunden
- `2` = Ungültiger oder nicht vorhandener `WorkspaceRoot`

#### CI-Integration

Das Skript wird im Workflow `.github/workflows/doc-naming-check.yml` auf `push` und `pull_request` ausgeführt.
