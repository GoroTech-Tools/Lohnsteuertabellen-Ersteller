# Technische Dokumentation – Lohnsteuertabellen-Ersteller

## 📐 Systemarchitektur

```bash
Lohnsteuertabellen-Ersteller/
├── src/
│   ├── generate_2026_tax_table.py      # Kern: Steuerberechnungen
│   ├── tax_table_gui.py                # GUI: Tkinter-Oberfläche
│   ├── app_icon.ico                    # Anwendungsicon
│   ├── build_exe.py                    # PyInstaller-Build-Skript
│   └── requirements.txt                 # Abhängigkeiten
├── docs/
│   ├── Liesmich.txt                         # Anwender-Dokumentation
│   ├── Dokumentation-Technik.md            # Diese Datei
│   ├── Dokumentation-Kalkulation.md        # Formeln, Parameter, Besonderheiten
│   └── Lizenz.txt                           # Lizenztext
├── build/                               # (bei EXE-Build erstellt)
├── dist/                                # (bei EXE-Build erstellt)
├── release/                             # ZIP-Release (bei EXE-Build erstellt)
└── ...
```

---

## 🔧 Module & Abhängigkeiten

### Kern-Abhängigkeiten

| Modul | Version | Zweck |
| --- | --- | --- |
| `pandas` | ≥1.3.0 | DataFrame-Verarbeitung, Datenexport |
| `openpyxl` | ≥3.0.0 | Excel-Dateien schreiben (`.xlsx`) |
| `tkinter` | stdlib | GUI-Framework |

### Build-Abhängigkeiten (optional)

| Modul | Zweck |
| --- | --- |
| `pyinstaller` | EXE-Packaging |
| `pyinstaller-hooks-contrib` | Extra-Hooks für spezielle Module |

---

## 📦 Modul-Beschreibung

### `generate_2026_tax_table.py`

**Hauptmodul** mit Steuerberechnung und Excel-Export.

#### Konfigurationen

```python
TAX_PARAMS_2026           # Dict mit Tarifparametern (BMF 2026)
KFB_VALUES                # Liste: [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4]
STEUERKLASSE_MULTIPLIKATOREN  # Dict: SK -> Faktor (1.0, 0.5, 1.5, ...)
```

#### Funktionen

```python
calculate_annual_tax(annual_income, tax_class) -> (tax, solidarity)
  Jahressteuer nach § 32a EStG basierend auf Tarifzonen.

calculate_monthly_tax(monthly_income, tax_class) -> (monthly_tax, monthly_solidarity)
  Monatliche Werte (= Jahreswert / 12).

calculate_church_tax(lohnsteuer) -> kist
  Kirchensteuer (9 % von Lohnsteuer).

generate_tax_records(monthly_income, tax_class, kfb_values) -> List[Dict]
  Erzeugt für eine Einkommensstufe Datensätze für alle KFB-Werte.

generate_2026_tax_table(
    income_min=1000,
    income_max=10000,
    step=5,
    tax_classes=None,
    kfb_values=None
) -> pd.DataFrame
  Hauptfunktion: Erstellt Rohdaten-DataFrame mit allen Kombinationen.

build_wide_dataframe(df) -> pd.DataFrame
  Transformiert Rohdaten in breite Tabelle (KFB als Spalten).

write_excel_file(output_path, wide_df, raw_df, main_sheet, raw_sheet) -> None
  Schreibt Excel mit Formatierung, zwei Blätter.
```

#### CLI-Interface

```python
def main()
  Kommandozeilenparser mit Argumenten:
    -o, --output: Dateipfad (default: Lohnsteuer_2026_West_monatlich.xlsx)
    --income-min: (default: 1000)
    --income-max: (default: 10000)
    --step: (default: 5)
```

---

### `tax_table_gui.py`

**GUI-Wrapper** mit Tkinter.

#### Konstanten

```python
ALLOWED_STEPS = (3, 5, 10, 50)
DEFAULT_YEAR, DEFAULT_STEP, DEFAULT_INCOME_MIN, DEFAULT_INCOME_MAX, DEFAULT_OUTPUT
  Standardwerte bei Reset.
```

#### Klasse: `TaxTableGui(tk.Tk)`

**Attribute:**

```python
self.year_var, self.step_var, self.income_min_var, self.income_max_var, self.output_var
  StringVar für Eingabefelder.
self.status_var
  Status-Anzeigelabel.
self.base_dir
  Pfad zum Script (für Icon-Suche).
```

**Methoden:**

```python
_set_app_icon()
  Lädt app_icon.ico (Windows).
  
_build_ui()
  Erzeugt Layout: Labels, Eingabefelder, Buttons.
  
_reset_fields()
  Setzt alle Felder auf Default zurück.
  
_choose_output()
  filedialog für Speicherort-Auswahl.
  
_resolve_output_path(year) -> Path
  Konvertiert Eingabe in absoluten Pfad + Dateiname.
  
_create_table()
  Validiert alle Eingaben, ruft Generator auf.
  Behandelt Fehler mit messagebox.
  
_open_documentation()
  Öffnet Technische Dokumentation im Browser/Editor.
```

#### Layout-Struktur

```text
Row 0: Jahr (YYYY) → Entry (16 chars)
Row 1: Schrittweite → Combobox (readonly, 3/5/10/50)
Row 2: Einkommen min → Entry
Row 3: Einkommen max → Entry
Row 4: Ausgabedatei → Entry + Button "Durchsuchen…"
Row 5: [Buttons] Zurücksetzen | Tabelle erstellen
Row 6: [Buttons] Hilfe | Dokumentation
Row 7: Status-Label
```

#### Validierungen

```text
Jahr:     int, 4-stellig
Schritt:  int, muss in ALLOWED_STEPS
Min/Max:  float (mit Komma-Konvertierung)
          ≥ 0
          max ≥ min
Output:   Path-Konvertierung, Verzeichnis-Erstellung
```

---

## 🧮 Tariflogik

### Tarifzonen (2026)

```text
Zone 1: Grundfreibetrag (12.384 €) < y ≤ 16.704 €
        Formel: (a*z + b*10000) * z, mit z = (y - gb) / 10000

Zone 2: 16.704 € < y ≤ 66.760 €
        Formel: (a + b*10000*z) * z + 1038.90

Zone 3: 66.760 € < y ≤ 287.000 €
        Formel: a + (y - gb2) * b (42% Satz)

Zone 4: y > 287.000 €
        Spitzensteuersatz (45%)
```

### Steuerklassen-Multiplikatoren

| SK | Name | Multiplikator | Anmerkung |
| --- | --- | --- | --- |
| 1 | Alleinstehend | 1.0 | Standard |
| 2 | Alleinerziehend | 1.0 | wie SK 1 |
| 3 | Verheiratet (höheres EK) | 0.5 | Ehegattensplitting |
| 4 | Verheiratet (ähnlich) | 1.0 | beide ~gleich |
| 5 | Verheiratet (niedriges EK) | 1.5 | Faktor erhöht |
| 6 | Mehrfachbeschäftigung | 1.0 | Nebeneinnahmen |

### Kinderfreibetrag (KFB)

**Vereinfachte Modellierung:**

- 1 KFB ≈ 50 € monatlich Einkommensreduktion
- KFB wird von Einkommen abgezogen vor Steuerberechnung
- Werte: 0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4

---

## 📊 DataFrame-Struktur

### Rohdaten (raw_df)

```text
Einkommen_EUR | Steuerklasse | Kinderfreibetrag | Lohnsteuer | SolZ | Kirchensteuer_9%
1000          | 1            | 0                | XX.XX      | X.XX | X.XX
1000          | 1            | 0.5              | XX.XX      | X.XX | X.XX
...
```

Größe bei Standard (1000–10000 €, Schritt 5):

- ~1,800 Einkommensstufen × 6 SK × 9 KFB-Werte = 97.200 Zeilen

### Breite Tabelle (wide_df)

```text
Einkommen_EUR | Steuerklasse | Lohnsteuer | KFB_0_SolZ | KFB_0_KiSt_9% | ...
1000          | 1            | XX.XX      | X.XX       | X.XX          | ...
```

Spalten: Einkommen, SK, Lohnsteuer + 9 KFB-Paare (SolZ + KiSt).

---

## 🔨 Build & Packaging

### PyInstaller-Konfiguration

**Datei: `src/build_exe.py`**

Wird von `src/` aus ausgeführt und erstellt EXE im `dist/`-Verzeichnis.

```bash
cd src
python build_exe.py
```

### Abhängigkeiten (src/requirements.txt)

```text
pandas>=1.3.0
openpyxl>=3.0.0
pyinstaller>=5.0
pyinstaller-hooks-contrib>=2022.0
```

### Build-Prozess

```bash
# 1. Abhängigkeiten installieren
pip install -r src/requirements.txt

# 2. Build ausführen
cd src
python build_exe.py

# 3. Artefakte
#    EXE: dist/Lohnsteuertabellen-Ersteller.exe
#    ZIP: release/Lohnsteuertabellen-Ersteller_<Version>.zip
```

### Automatisches Release-Packaging

Nach erfolgreichem PyInstaller-Lauf erstellt `build_exe.py` automatisch ein ZIP-Archiv im Projektbasisverzeichnis unter `release/`.

**Inhalt des ZIP-Pakets:**

- `Lohnsteuertabellen-Ersteller.exe`
- vollständiges Verzeichnis `docs/`

Damit sind Anwendung und Dokumentation immer in einem verteilbaren Artefakt gebündelt.

---

## 🚀 Installation & Ausführung

### Variante A: EXE (standalone, empfohlen)

- **Datei:** `dist/Lohnsteuertabellen-Ersteller.exe`
- **Größe:** ~56 MB (alles inkludiert)
- **Voraussetzungen:** Windows 7+
- **Start:** Doppelklick auf EXE

Keine weitere Installation erforderlich.

### Variante B: Python-Quellcode

- **Dateien:** `src/tax_table_gui.py` + `src/generate_2026_tax_table.py`
- **Voraussetzungen:** Python 3.8+, pandas, openpyxl
- **Start:**

  ```bash
  cd src
  python tax_table_gui.py
  ```

---

## 🧪 Testing & Entwicklung

### Manuelles Testen (GUI)

```bash
cd src
python tax_table_gui.py

# Testszenarien:
# - Standard-Einstellungen → OK
# - Min > Max → Fehler erwartung
# - Ungültige Schrittweite → Fehler erwartung
# - Fehlende BMF-Daten (z.B. Jahr 2025) → Warnung + Abbruch
```

### Unit-Tests (künftig)

```python
# tests/test_calculations.py
def test_annual_tax_zero_income():
    tax, solz = calculate_annual_tax(0, 1)
    assert tax == 0.0
    assert solz == 0.0

def test_annual_tax_high_income():
    # Testfall mit bekanntem Ergebnis
    tax, solz = calculate_annual_tax(100000, 1)
    # Prüfung gegen BMF-Berechnung
```

### Performance

**Messungen (bei Standard 1000–10000, Schritt 5):**

- Daten generieren: ~2–3 Sekunden
- DataFrame-Transformation: ~1 Sekunde
- Excel schreiben: ~2–3 Sekunden
- **Gesamt GUI:** ~6–8 Sekunden (sichtbar im Status)

Bei größeren Bereichen (z.B. 1000–100000, Schritt 3):

- Datensätze: ~1,6 Mio
- Zeit: 60–90 Sekunden (progressbar wünschenswert)

---

## 🔐 Sicherheit & Datenschutz

- **Eingabe-Validierung:** Alle Nutzereingaben werden vor Verarbeitung geprüft
- **Keine Netzwerk-Kommunikation:** Offline-Tool
- **Dateirechte:** Nutzer kann Speicherort wählen
- **Fehlerbehandlung:** Exceptions werden abgefangen, keine Stack-Traces in GUI

---

## 🐛 Troubleshooting

### Problem: EXE startet nicht

**Lösung 1:** Firewall/Antivirus prüfen (häufig bei neu erstellten Binaries)

**Lösung 2:** In Admin-Modus starten

```bash
Rechtsklick → "Als Administrator ausführen"
```

**Lösung 3:** Windows Defender SmartScreen deaktivieren (temporär)

```bash
Sicherheitscenter → App-Kontrolle → SmartScreen → Aus
```

### Problem: "Error: No module named 'pandas'"

**Lösung:** Abhängigkeiten nachinstallieren:

```bash
pip install pandas openpyxl --upgrade
```

### Problem: GUI ist langsam

Das ist normal bei sehr großen Tabellen (>50 Mio. Datensätze).

**Workaround:** Schrittweite erhöhen (z.B. 50 € statt 5 €).

### Problem: Icon wird nicht angezeigt

Das Icon ist optional. Anwendung funktioniert auch ohne.

---

## 📤 Verteilung

### Für Endnutzer (Empfehlung)

Verteilen Sie bevorzugt das automatisch erzeugte **ZIP-Release**:

```text
release/Lohnsteuertabellen-Ersteller_<Version>.zip
```

Nach dem Entpacken sind EXE und alle Doku-Dateien direkt verfügbar.

### Für Entwickler

Verteilen Sie das **gesamte Repository**:

```text
Lohnsteuertabellen-Ersteller/
├── src/
├── docs/
├── build/
├── dist/
└── ...
```

Entwickler können eigene EXE bauen oder im Python-Modus arbeiten.

---

## 🔐 Sicherheit bei Verteilung

1. **EXE signieren** (optional, für Vertrauen):

   ```bash
   signtool sign /f cert.pfx /t http://timestamp.server.com Lohnsteuertabellen-Ersteller.exe
   ```

2. **Checksumme bereitstellen** (Integrität prüfen):

   ```bash
   certUtil -hashfile Lohnsteuertabellen-Ersteller.exe SHA256
   ```

   Ausgabe in Release-Notes dokumentieren.

3. **Versionsnummer** in Dateinamen (z.B. `Lohnsteuertabellen-Ersteller_v1.0.exe`)

---

## 📝 Erweiterungen & Roadmap

### Geplant

1. **Weitere Jahrgänge:** Wenn BMF-Formeln verfügbar (z.B. 2025, 2027)
2. **Fortschrittsanzeige:** Bei längeren Generierungen
3. **Export-Formate:** CSV, JSON zusätzlich zu Excel
4. **Historische Vergleiche:** Mehrere Jahre in einer Datei
5. **Keyboard-Shortcuts:** z.B. Alt+R für Reset, Ctrl+S für Speichern

### Technische Schulden

- [ ] Unit-Tests für alle Funktionen
- [ ] Type-Hints vollständig (noch teilweise `Any`)
- [ ] Logging-Modul statt print()
- [ ] Konfigurationsdatei für BMF-Parameter (nicht hardcoded)

---

## 🐛 Bekannte Limitierungen

1. **Vereinfachte Steuerklassen-Multiplikatoren:** Vereinfachung, nicht 100% amtlich
2. **KFB-Modell:** Linear vereinfacht (50 €/KFB), nicht alle Feinheiten
3. **Keine Lohn-Grenzen:** Z.B. Mindestlohn, Gleitzone nicht berücksichtigt
4. **GUI Single-Thread:** Lange Generierungen können UI einfrieren (60+ Sek)
5. **Keine Abbruch-Option:** Laufende Generierung kann nicht unterbrochen werden

---

## 📚 Referenzen

- **BMF Einkommensteuer-Tarifformeln 2026:** [Bundesfinanzhof](https://www.bundesfinanzhof.de/)
- **§ 32a EStG:** Einkommensteuergesetz
- **pandas Dokumentation:** [pandas.pydata.org](https://pandas.pydata.org/)
- **Tkinter Dokumentation:** [docs.python.org](https://docs.python.org/3/library/tkinter.html)

---

**Version:** 1.0.26115.19430  
**Stand:** 25.04.2026  
**Autor:** GoroTech  
**Lizenz:** Frei – Nutzung, Weitergabe und Anpassung ohne Einschränkungen gestattet.  
**Zielentwickler:** Python 3.8+
