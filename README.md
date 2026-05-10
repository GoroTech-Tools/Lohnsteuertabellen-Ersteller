# Lohnsteuertabellen-Ersteller

Ein benutzerfreundliches Tool zum Erstellen von Lohnsteuertabellen nach aktuellen BMF-Tarifformeln. Mit grafischer Oberfläche einfach Tabellen mit individuellen Parametern erzeugen.

## ✨ Funktionen

- **Schlichte GUI** – ohne unnötige Komplexität
- **Flexible Einkommensbereich** – min/max frei wählbar
- **Mehrere Schrittweiten** – 3, 5, 10 oder 50 €
- **Automatische Excel-Generierung** – mit strukturierter Formatierung
- **Offline-Betrieb** – keine Internetverbindung erforderlich
- **Speicherort wählbar** – Dialog zur Dateisicherung
- **Validierung** – intelligente Plausibilitätsprüfung der Eingaben

## 📋 Eingaben

| Feld | Standard | Beschreibung |
| --- | --- | --- |
| **Jahr** | 2026 | Unterstützte Jahre: 2006–2026 |
| **Schrittweite** | 5 € | Erlaubt: 3, 5, 10, 50 € |
| **Einkommen min** | 1.000 € | Tabellenbeginn (EUR/Monat) |
| **Einkommen max** | 10.000 € | Tabellenende (EUR/Monat) |
| **Speicherort** | `.` (aktuell) | Zielverzeichnis oder Dateiname |

## 🚀 Quickstart

### Mit GUI (empfohlen)

1. **Anwendung starten:**

   ```bash
   python tax_table_gui.py
   ```

   oder (ab Build): `Lohnsteuertabellen-Ersteller.exe`

2. **Parameter einstellen:**

   - Jahr: `2026` (oder ein anderes unterstütztes Jahr)
   - Schrittweite: `5` (oder 3, 10, 50)
   - Einkommen: min `1000` – max `10000`
   - Speicherort: `Durchsuchen…` oder `.` (lokal)

3. **Klick „Tabelle erstellen"** – fertig!

4. **Zurücksetzen möglich** – Button „Zurücksetzen" für schnelle Testreihen

### Kommandozeile

```bash
python generate_2026_tax_table.py \
   -o "Lohnsteuer_2026_West_monatlich.xlsx" \
  --income-min 800 \
  --income-max 15000 \
  --step 10
```

## 📊 Ausgabe

Erzeugte Excel-Datei (`*.xlsx`) mit zwei Blättern:

### Blatt „Lohnsteuer_[Jahr]"

Kompakte Darstellung mit Spalten:

- Einkommen (EUR)
- Steuerklasse (1–6)
- Lohnsteuer (€)
- KFB-0 bis KFB-4 (Solz + Kirchensteuer)

### Blatt „Lohnsteuer_Rohdaten_[Jahr]"

Detaillierte Rohdaten mit allen Kombinationen:

- Einkommen, Steuerklasse, Kinderfreibetrag
- Lohnsteuer, Solidaritätszuschlag, Kirchensteuer (9%)

## ⚙️ Berechnungsgrundlagen

**Quelle:** BMF/PAP-Daten je ausgewähltem Jahr (aktuell: 2006–2026)

- **Grundfreibetrag:** 12.348 €
- **Solidaritätszuschlag:** 5,5 % mit Freigrenze/Milderungszone
- **Kirchensteuer:** 9 % (auf Lohnsteuer)
- **Steuerklassen:** 1–6 mit steuerklassenspezifischer Berechnungslogik (u. a. Splitting/Abzugsregeln)
- **Kinderfreibeträge:** 0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4

## ✅ Validierungen

Die GUI prüft vor der Generierung:

- ✓ Jahr gültig (4-stellig)
- ✓ Schrittweite erlaubt (3/5/10/50)
- ✓ Einkommen min/max sind Zahlen
- ✓ Einkommen ≥ 0 €
- ✓ Einkommen max ≥ min
- ✓ BMF-Tarifdaten für das Jahr vorhanden

Bei Verstößen → klare Fehlermeldung.

## 🔄 Voraussetzungen

- **Python 3.13+** (für Quellcode-Betrieb)
- **pandas, openpyxl** (automatisch bei Setup)
- **Windows/macOS/Linux** (EXE nur Windows)
- **Icon:** `src/app_icon.ico` (optional, Fallback auf Standard)

## 🛠️ Installation & Ausführung

### Variante 1: GUI-Direktstart (schnell)

```bash
cd src
python tax_table_gui.py
```

### Variante 2: Kommandozeilen-Tool

```bash
cd src
python generate_2026_tax_table.py -o "Ausgabe.xlsx"
```

### Variante 3: EXE (Windows, standalone)

```bash
Lohnsteuertabellen-Ersteller.exe
```

## Verwendung mit der Lohn- und Gehaltsabrechnung

Die mit diesem Tool erstellten Lohnsteuertabellen sind für die Nutzung innerhalb der Microsoft Excel-Arbeitsmappe **„Lohn- und Gehaltsabrechnungen 2026.xlsm"** vorgesehen. Die Arbeitsmappe verweist auf die erzeugten Tabellen und nutzt die Steuerwerte für die automatisierte Lohn- und Gehaltsabrechnung.

- **Zieldatei:** `Lohn- und Gehaltsabrechnungen 2026.xlsm`
- **Empfohlener Speicherort:** Selbes Verzeichnis wie die Arbeitsmappe oder ein eingetragener Suchpfad innerhalb der Mappe
- **Vorgehensweise:** Tabelle mit diesem Tool erzeugen → Datei im vorgesehenen Ordner ablegen → Excel-Mappe öffnen, ggf. Verknüpfungen aktualisieren

---

## 📦 Release-Paket (automatisch nach Build)

Nach jedem erfolgreichen Build wird zusätzlich zur EXE automatisch ein ZIP-Release erzeugt.

- **Pfad:** `release/Lohnsteuertabellen-Ersteller_<Version>.zip`
- **Inhalt:** `Lohnsteuertabellen-Ersteller.exe` + komplettes Verzeichnis `docs/`

Damit steht für die Verteilung immer ein kompaktes Paket mit Anwendung und Dokumentation bereit.

## 📝 Häufige Fragen

**F: Kann ich Werte zwischen den Standard-Schrittweiten nutzen?**  
A: Nein, erlaubt sind nur 3, 5, 10, 50 €. Das verhindert unnötig lange Tabellen.

**F: Welche Steuerklassen werden berücksichtigt?**  
A: Alle 6 (alleinstehend bis mehrfachbeschäftigung) mit steuerklassenspezifischer Berechnungslogik.

**F: Für welche Jahre gibt es Daten?**  
A: Aktuell 2006 bis 2026. Die Auswahl erfolgt in der GUI dynamisch über `src/available_tax_years.py`.

**Hinweis für Entwickler:** Das Standardjahr sowie Blatt- und Dateinamen werden zentral in `src/tax_year_config.py` gepflegt.

Die universelle Generierung läuft über `src/generate_tax_tables_universal.py`; der 2026-Wrapper in `src/generate_2026_tax_table.py` bleibt für Rückwärtskompatibilität erhalten.

Welche Jahre in der Oberfläche auswählbar sind, wird zentral in `src/available_tax_years.py` gesteuert.

Vorbereitete, aber noch nicht freigegebene Jahre (z. B. 2027-Template) werden dort separat als inaktiv geführt und nicht in der GUI angezeigt.

Den Aktivierungsstatus eines vorbereiteten Jahres können Entwickler direkt prüfen:

```powershell
cd src
py -3 -m available_tax_years --check 2027
```

**F: Ist die Berechnung amtlich?**  
A: Die Formeln folgen den BMF-Parametern, bilden aber eine vereinfachte Annäherung. Für offizielle Zwecke: BMF-Originalquellen konsultieren.

**F: Kann ich eine laufende Generierung abbrechen?**  
A: Im Moment nicht. Fenster schließen beendet den Prozess (bei langen Tabellen ggf. zu langsam).

## 📞 Support & Entwicklung

- **Projekt:** GitHub-Repository
- **Dokumentation:** `Technische Dokumentation.md` für Entwickler
- **Issues/Fehler:** In Repository posten

## 📄 Lizenz

Frei – Nutzung, Weitergabe und Anpassung ohne Einschränkungen gestattet.

## 🗒️ Änderungsstand

- **10.05.2026 (v1.1.1):** Multi-Year-Support (2006–2026) und PAP-Parser-Standard dokumentiert; Dokumentation auf aktuelle Modulstruktur abgeglichen.
- **09.05.2026 (v1.0.2):** Kirchensteuerberechnung korrigiert – KiSt wird jetzt wie der SolZ auf Basis des um den Kinderfreibetrag reduzierten Einkommens berechnet. Verweis auf Excel-Arbeitsmappe „Lohn- und Gehaltsabrechnungen 2026.xlsm" ergänzt.

---

**Version:** 1.1.1  
**Stand:** 10.05.2026  
**Autor:** GoroTech
