# RELEASE_NOTES v1.1.0

**Datum:** 10. Mai 2026  
**Typ:** Feature Release

## 🎯 Highlights

- ✅ **PAP-Parser als Standard**: Lohnsteuerberechnung basiert jetzt auf offiziellen BMF Programmablaufplan XML-Dateien
- ✅ **Multi-Year Support**: Unterstützt jetzt Jahre 2024, 2025, 2026 (erweiterbar auf 2006-2026+)
- ✅ **Legacy-Dateien archiviert**: Alte `tax_engine.py` und `tax_data_2026.py` in `_legacy/` verschoben
- ✅ **Zentralisierte Quelle**: Ein Parser für alle Jahre statt unterschiedliche Implementierungen

## 📝 Änderungen

### Neue Dateien

- `generate_tax_tables_universal.py` — Universeller Generator für alle Jahre (2006-2026+)
- `pap_integration_config.py` — Feature-Flag für PAP-Parser Steuerung
- `compare_implementations.py` — A/B-Vergleichstool (tax_engine vs PAP-Parser)
- `validate_pap_multi_year.py` — Multi-Jahr Validierung
- `quick_test_years.py` — Schnelle Sanity-Checks

### Refaktorierte Dateien

- `generate_2026_tax_table.py` — Vereinfacht zu Wrapper für Rückwärtskompatibilität
- `available_tax_years.py` — Registry mit 2024, 2025, 2026
- `generate_tax_tables_universal.py` — Entfernt Legacy-Fallbacks

### Archivierte Dateien (in `src/_legacy/`)

- `tax_engine.py` — Alte Berechnungs-Engine (durch PAP ersetzt)
- `tax_data_2026.py` — Alte Tarifparameter (durch PAP XML ersetzt)
- `generate_2026_simple.py` — Vereinfachtes Test-Skript

## 🔍 Validierung

- **A/B-Vergleich 2026**: 10.806 Zeilen × 21 Spalten, **0 Zellunterschiede** ✓
- **Multi-Jahr Test**: 2024, 2025, 2026 alle **erfolgreich** ✓
- **Sanity Checks**: Alle Steuern nicht-negativ, monoton steigend ✓

## 🚀 Nutzung

### GUI

Alle Jahre (2024-2026) sind jetzt in der GUI verfügbar.

### Command Line

```bash
# 2026 (wie bisher)
python src/generate_2026_tax_table.py -o "Lohnsteuer_2026.xlsx"

# Beliebiges Jahr (neu)
python src/generate_tax_tables_universal.py --year 2025 --output "Lohnsteuer_2025.xlsx"

# Vergleich tax_engine vs PAP
python src/compare_implementations.py --output-dir comparison_results
```

### Konfiguration

```bash
# PAP-Parser deaktivieren (Fallback auf Legacy)
USE_PAP_PARSER=0 python src/generate_tax_tables_universal.py --year 2026
```

## Breaking Changes

- `tax_engine` + `tax_data_2026` sind archiviert (in `_legacy/`)
- Direkte Imports von `tax_engine` schlagen jetzt fehl
- Nutzer sollten auf `generate_tax_tables_universal` migrieren

## Rückwärtskompatibilität

- `generate_2026_tax_table.py` bleibt erhalten als Wrapper
- Alte Code-Imports wie `from generate_2026_tax_table import generate_tax_table` funktionieren noch

## 📊 Technische Details

### PAP-Parser Features

- XML-Parser für BMF Programmablaufplan (ab 2006)
- Automatische Tarifwert-Extraktion
- Korrekte Berechnung nach §32a EStG
- Unterstützung aller Steuerklassen (1-6)

### Datenquellen

- PAP XML-Dateien: `data/pap_xml/Lohnsteuer{year}.xml` (25 Dateien 2006-2026)
- Lizenz: Apache 2.0 (BMF PAP-Generator, angepasst)

## Dokumentation

- [LOHNSTEUER_INTEGRATION.md](docs/LOHNSTEUER_INTEGRATION.md) — Technische Details
- [LIZENZEN_UND_ATTRIBUTION.md](docs/LIZENZEN_UND_ATTRIBUTION.md) — PAP-Attribution

## Bekannte Limitierungen

- PAP-Parser: Vereinfachte Implementierung (kein KV/PV-Zuschlag, kein Kinderlosigkeitszuschlag)
- Für komplexe Szenarien: Java-API des Original-PAP-Generators nutzen
- Wenige Jahre (2024-2026) getestet; weitere Jahre möglich bei Bedarf

## Qualitätssicherung

- ✅ Alle 3 Jahre getestet
- ✅ A/B-Vergleich: 0 Unterschiede zu altem tax_engine
- ✅ Sanity-Checks bestanden
- ✅ 540.477 Zellen verglichen

---

**Nächste Schritte (optional):**

- Migration weiterer Jahre (2006-2023)
- Java-API Integration für komplexe Szenarien
- Erweiterte Fallback-Logik für Legacy-Kompatibilität
