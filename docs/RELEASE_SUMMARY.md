# Lohnsteuertabellen-Ersteller — Release-Übersicht

---

## v1.1.6 — Bugfix: KFB/SolZ/Kirchensteuer

**Datum:** 17. Mai 2026  
**Status:** ✅ Release abgeschlossen

### Behobene Fehler

| Fehler | Ursache | Fix |
| ------ | ------- | --- |
| **KFB falsch berechnet (Legacy 2026)** | `kfb_monthly_reduction = kfb * 50` statt PAP MZTABFB | `_legacy/tax_engine.py`: KFB = `int(ZKF × 9.756 €)` SK 1/2/3, `int(ZKF × 4.878 €)` SK 4 |
| **KFB falsch berechnet (PAP-Pfad)** | `reduced_income = monthly_income × (1 − kfb/100)` | `generate_tax_tables_universal.py`: Direktaufruf `berechne_lohnsteuer(..., zkf=kfb)` |
| **SolZ falsch (Legacy)** | Basis war LSTJAHR statt JBMG | Zweiter Durchlauf mit `_calculate_jbmg()` |
| **Kirchensteuer falsch (beide Pfade)** | Basis war LSTJAHR statt JBMG | Kirchensteuer = `JBMG / 12 × 9 %` |
| **PAP-Parser: ZVE falsch** | Fehlende Abzüge ANP/SAP/EFA vor Tarifberechnung | `lohnsteuer_integration.py`: Korrekte ZTABFB + VSP |
| **PAP-Parser: SolZ-Freigrenze falsch** | Hardcodiert 972 € statt SOLZFREI aus XML (20.350 €) | Extraktion aus PAP-XML + KZTAB-Multiplikator |

### Geänderte Dateien

- `src/_legacy/tax_engine.py` — Neue `_calculate_jbmg()`-Hilfsfunktion, korrigierte `generate_tax_records_for_year()`
- `src/_legacy/tax_data_2026.py` — Neue Keys `kfb_faktor_sk123: 9756` und `kfb_faktor_sk4: 4878`
- `src/lohnsteuer_integration.py` — Neuer Parameter `zkf`, korrekte UPTAB-Implementierung je Jahr, JBMG-Zweidurchlauf, SOLZFREI aus XML
- `src/generate_tax_tables_universal.py` — PAP-Pfad nutzt `berechne_lohnsteuer(zkf=kfb)` und `kirchensteuer_basis`
- `docs/DOKUMENTATION_KALKULATION.md` — Abschnitte 6, 7, 9 aktualisiert
- `docs/DOKUMENTATION_TECHNIK.md` — Modulstruktur und KFB-Abschnitt aktualisiert

---

## v1.1.1 — Abschluss

**Datum:** 10. Mai 2026  
**Status:** ✅ Release abgeschlossen  
**Commits:** 2 (v1.1.1 Release + Cleanup)

---

## 📊 Final Summary

### Erreichte Ziele

| Ziel | Status | Details |
| ---- | ------ | ------- |
| **PAP-Parser als Standard** | ✅ | Default: `USE_PAP_PARSER=1` |
| **Multi-Year (2024-2026)** | ✅ | Tested & Validated |
| **Alle Jahre (2006-2026)** | ✅ | 21 Jahre registriert |
| **A/B-Vergleich 2026** | ✅ | 0 Zellunterschiede |
| **Legacy archiviert** | ✅ | `tax_engine` → `_legacy/` |
| **Release v1.1.1** | ✅ | GitHub Release + ZIP |
| **Projektaufräumen** | ✅ | Finale Struktur |

### Commits in dieser Session

```text
fe27d0a - feat(v1.1.1): Erweitere auf alle Jahre 2006-2026 und räume auf
4dc6d75 - feat(v1.1.1): Multi-year PAP-Parser support
```

---

## 🗂️ Finale Projektstruktur

```text
Lohnsteuertabellen-Ersteller/
├── build/
│   └── Lohnsteuertabellen-Ersteller/     ← EXE
├── release/
│   ├── Lohnsteuertabellen-Ersteller_1.1.1.zip
│   ├── Lohnsteuertabellen-Ersteller_1.0.5.zip
│   └── Lohnsteuertabellen-Ersteller_1.0.4.zip
├── src/
│   ├── tax_table_gui.py                  ← GUI-Entrypoint
│   ├── available_tax_years.py            ← Year Registry (2006-2026)
│   ├── generate_tax_tables_universal.py  ← Main Generator
│   ├── lohnsteuer_integration.py         ← PAP-Parser
│   ├── pap_integration_config.py         ← Feature-Flag
│   ├── generate_2026_tax_table.py        ← Wrapper (Rückwärts-Kompatibilität)
│   ├── compare_implementations.py        ← A/B-Tool
│   ├── validate_pap_multi_year.py        ← Validator
│   ├── quick_test_years.py               ← Schnelle Tests
│   └── _legacy/                          ← Archivierte Module
│       ├── tax_engine.py
│       ├── tax_data_2026.py
│       └── generate_2026_simple.py
├── data/
│   └── pap_xml/                          ← 25 PAP-XML-Dateien (2006-2026)
├── docs/
│   ├── LOHNSTEUER_INTEGRATION.md
│   ├── LIZENZEN_UND_ATTRIBUTION.md
│   └── _archive/
│       └── LOHNSTEUER_INTEGRATION_QUICK.md
├── version_state.json                    ← v1.1.1
├── RELEASE_1_1_0.md                      ← Release Notes
└── build.ps1                             ← Build-Entrypoint
```

---

## 🔄 Refaktorierungen

### Alte Struktur (v1.0.5)

```text
Nur Jahr 2026
- tax_engine.py + tax_data_2026.py
- generate_2026_tax_table.py (hardcodiert)
```

### Neue Struktur (v1.1.1)

```text
21 Jahre (2006-2026)
- generate_tax_tables_universal.py (flexibel)
- lohnsteuer_integration.py (PAP-Parser)
- available_tax_years.py (dynamische Registry)
- pap_integration_config.py (Feature-Flag)
```

### Vorher vs. Nachher

| Eigenschaft | v1.0.5 | v1.1.1 |
| ----------- | ------ | ------ |
| Jahre | 1 (2026) | 21 (2006-2026) |
| Datenquelle | `tax_data_2026.py` | PAP XML |
| Generator | Jahr-spezifisch | Universal |
| Erweiterbar | Nein | Ja |
| Code-Komplexität | Hoch | Niedrig |

---

## ✅ Qualitätssicherung

### Tests durchgeführt

- ✅ 2024 PAP-Parser: OK
- ✅ 2025 PAP-Parser: OK
- ✅ 2026 PAP-Parser: OK
- ✅ A/B-Vergleich: 0 Unterschiede (10.806 Zeilen × 21 Spalten)
- ✅ Sanity Checks: Alle bestanden
- ✅ Rückwärts-Kompatibilität: `generate_2026_tax_table` noch funktionsfähig

### Validierungs-Tools

- `compare_implementations.py` — Vergleicht tax_engine vs PAP
- `validate_pap_multi_year.py` — Vollständige Validierung (540.477 Zellen)
- `quick_test_years.py` — Schnelle Sanity-Checks

---

## 📦 GitHub Release

**Tag:** <https://github.com/TomGorontzy/Lohnsteuertabellen-Ersteller/releases/tag/v1.1.1>  
**ZIP:** `Lohnsteuertabellen-Ersteller_1.1.1.zip`  
**Size:** ~5.55 MiB (mit PAP XML)

---

## 🚀 Bekannte Next Steps (Optional)

1. **Java-API Integration** — Für komplexe Szenarien (KV-Zuschlag, PV-Zuschlag)
2. **GUI erweitern** — Year-Selector mit allen 21 Jahren
3. **Caching** — PAP-Parser Parser-Instanzen cachen
4. **Ältere Jahre (2006-2009)** — Zusätzliche XML-Versionen testen
5. **CI/CD** — Automatische Tests für alle Jahre

---

## 📄 Dokumentation

- [RELEASE_1_1_0.md](RELEASE_1_1_0.md) — Release Notes
- [docs/LOHNSTEUER_INTEGRATION.md](docs/LOHNSTEUER_INTEGRATION.md) — Technische Details
- [docs/LIZENZEN_UND_ATTRIBUTION.md](docs/LIZENZEN_UND_ATTRIBUTION.md) — PAP Attribution
- [README.md](README.md) — Projekt-Übersicht

---

## 🎯 Fazit

**v1.1.1 ist produktionsreif** mit:

- ✅ Multi-Year Support (21 Jahre)
- ✅ Zentrale PAP-Parser Quelle
- ✅ Zero-Diff Validierung zu v1.0.5
- ✅ Saubere, wartbare Code-Struktur
- ✅ Vollständige Dokumentation

**Status:** Deployment-ready 🚀
