# Technische Dokumentation – Lohnsteuertabellen-Ersteller

## 📐 Systemarchitektur

```bash
Lohnsteuertabellen-Ersteller/
├── src/
│   ├── generate_2026_tax_table.py      # Kern: Steuerberechnungen
│   ├── tax_table_gui.py                # GUI: Tkinter-Oberfläche
│   ├── app_icon.ico                    # Anwendungsicon
│   ├── build_exe.py                    # PyInstaller-Build-Skript
├── requirements.txt                     # Abhängigkeiten
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
AVAILABLE_GENERATORS      # Dict: Jahr -> Generatorfunktion (aktuell 2026)
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
  
_open_user_manual(), _open_tech_docs()
  Öffnen Anwender- bzw. Technikdokumentation (embedded oder Dateisystem).
```

#### Layout-Struktur

```text
Row 0: Jahr (YYYY) → Entry (16 chars)
Row 1: Schrittweite → Combobox (readonly, 3/5/10/50)
Row 2: Einkommen min → Entry
Row 3: Einkommen max → Entry
Row 4: Ausgabedatei → Entry + Button "Durchsuchen…"
Row 5: [Buttons] Zurücksetzen | Tabelle erstellen
Row 6: [Buttons] Anwender-Hilfe | Technische Doku
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

### Tarifzonen (2026, gemäß Implementierung)

```text
Zone 1: zvE ≤ 12.348 €
  S = 0

Zone 2: 12.349 € – 17.799 €
  S = (914,51 · y + 1.400) · y
  y = (zvE - 12.348) / 10.000

Zone 3: 17.800 € – 69.878 €
  S = (173,10 · z + 2.397) · z + 1.034,87
  z = (zvE - 17.799) / 10.000

Zone 4: 69.879 € – 277.825 €
  S = 0,42 · x - 11.135,63

Zone 5: ab 277.826 €
  S = 0,45 · x - 19.470,38
```

### Steuerklassen-Logik (ohne Multiplikator-Modell)

| SK | Umgesetzte Logik |
| --- | --- |
| 1/4 | Grundtarif mit AN-Pauschbetrag, Sonderausgaben-Pauschbetrag und Vorsorgepauschale |
| 2 | Wie SK 1/4, zusätzlich Entlastungsbetrag für Alleinerziehende |
| 3 | Ehegattensplitting: $2 \times$ Grundtarif($zvE/2$) |
| 5 | Kein GFB/kein AN-Pauschbetrag; Berechnung über $zvE +$ Grundfreibetrag |
| 6 | Wie SK 5, zusätzlich ohne Vorsorgepauschale |

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

### Abhängigkeiten (requirements.txt im Projektroot)

```text
pandas>=1.3.0
openpyxl>=3.0.0
pyinstaller>=5.0
pyinstaller-hooks-contrib>=2022.0
```

### Build-Prozess

```bash
# 1. Abhängigkeiten installieren
pip install -r requirements.txt

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

## 📅 Anpassung für ein neues Steuerjahr (2027 ff.)

Wenn das BMF den Programmablaufplan für ein neues Jahr veröffentlicht (üblicherweise im November des Vorjahres unter [bundesfinanzministerium.de](https://www.bundesfinanzministerium.de)), sind folgende Schritte erforderlich.

### Schritt 1 – Neue Tarifparameter ermitteln

Aus dem BMF-Programmablaufplan des neuen Jahres folgende Werte ablesen:

| Parameter | Wo im PAP | Beispiel 2026 |
| --------- | --------- | ------------- |
| `grundfreibetrag` | § 32a-Tarifzonen, Grenze Zone 1 | 12.348 € |
| `grenze_zone2` | Obergrenze 1. Progressionszone | 17.799 € |
| `grenze_zone3` | Obergrenze 2. Progressionszone | 69.878 € |
| `grenze_zone4` | Obergrenze Proportionalzone 42 % | 277.825 € |
| `zone2_a`, `zone2_b` | Koeffizienten 1. Progressionszone | 914,51 / 1.400,00 |
| `zone3_a`, `zone3_b`, `zone3_T1` | Koeffizienten 2. Progressionszone | 173,10 / 2.397,00 / 1.034,87 |
| `zone4_rate`, `zone4_offset` | 42 %-Proportionalzone | 0,42 / 11.135,63 |
| `zone5_rate`, `zone5_offset` | 45 %-Spitzenzone | 0,45 / 19.470,38 |
| `arbeitnehmer_pauschbetrag` | § 9a EStG | 1.230 € |
| `sonderausgaben_pauschbetrag` | § 10c EStG | 36 € |
| `entlastungsbetrag_alleinerziehend` | § 24b EStG | 4.260 € |
| `rv_an_satz`, `bbg_rv` | SV-Rechengrößen-VO | 9,30 % / 89.400 € |
| `kv_an_satz`, `pv_an_satz`, `bbg_kv` | GKV-Beitragssatz / SV-Rechengrößen | 8,15 % / 1,80 % / 66.150 € |

> **Tipp:** Die KV-Zusatzbeitragssätze variieren je Kasse. Im vereinfachten Modell wird ein mittlerer Zusatzbeitrag (~1,6 %) auf den halbierten Basissatz addiert. Den aktuellen Durchschnittswert veröffentlicht das BMG jährlich.

### Schritt 2 – Neues Generator-Modul anlegen

```bash
# Vorlage kopieren
copy src\generate_2026_tax_table.py src\generate_2027_tax_table.py
```

In `src/generate_2027_tax_table.py` ersetzen:

1. Den Dict-Namen `TAX_PARAMS_2026` → `TAX_PARAMS_2027` (alle Vorkommen).
2. Alle Parameterwerte im Dict durch die neuen BMF-Werte aus Schritt 1.
3. Den Funktionsnamen `_grundtarif_2026` → `_grundtarif_2027` (alle Vorkommen).
4. Den Funktionsnamen `generate_2026_tax_table` → `generate_2027_tax_table` (alle Vorkommen).
5. Den Docstring/Kommentar-Jahrgang im Kopf der Datei.

### Schritt 3 – GUI einbinden

In `src/tax_table_gui.py` drei Änderungen vornehmen:

```python
# 1. Import ergänzen
from generate_2027_tax_table import (
    generate_2027_tax_table,
    build_wide_dataframe,
    write_excel_file,
)

# 2. Wrapper-Funktion hinzufügen (analog zu generate_for_2026)
def generate_for_2027(output_path: Path, step: int, income_min: float, income_max: float) -> None:
    """Erzeugt die 2027er-Tabelle und schreibt sie als Excel-Datei."""
    raw_df = generate_2027_tax_table(step=step, income_min=income_min, income_max=income_max)
    wide_df = build_wide_dataframe(raw_df)
    write_excel_file(output_path, wide_df, raw_df,
                     main_sheet="Lohnsteuer 2027", raw_sheet="Rohdaten 2027")

# 3. Neues Jahr in AVAILABLE_GENERATORS eintragen und DEFAULT_YEAR aktualisieren
AVAILABLE_GENERATORS: Dict[int, GeneratorFn] = {
    2026: generate_for_2026,
    2027: generate_for_2027,   # neu
}
DEFAULT_YEAR = "2027"
```

### Schritt 4 – Kalkulationsdokumentation aktualisieren

In `docs/Dokumentation-Kalkulation.md` den Kopfbereich anpassen:

```markdown
**Rechtsgrundlage:** § 32a EStG in der Fassung ab Veranlagungszeitraum 2027
**Quelle Tarifformeln:** BMF-Programmablaufplan 2027 (Anlage 2), veröffentlicht …
**Gültig ab:** 1. Januar 2027
```

Alle Zahlenwerte in den Tabellen (Tarifzonen, Vorsorgepauschale, Freibeträge) durch die neuen Werte ersetzen.

### Schritt 5 – EXE neu bauen

```bash
cd src
python build_exe.py
```

Das erzeugte Release-ZIP in `release/` enthält automatisch die aktualisierte Dokumentation.

### Checkliste

- [ ] BMF-PAP für neues Jahr heruntergeladen und Werte abgelesen
- [ ] `src/generate_<YYYY>_tax_table.py` angelegt und alle Parameter aktualisiert
- [ ] `tax_table_gui.py` – Import, Wrapper-Funktion und `AVAILABLE_GENERATORS` ergänzt
- [ ] `DEFAULT_YEAR` auf neues Jahr gesetzt
- [ ] `docs/Dokumentation-Kalkulation.md` – Zahlenwerte aktualisiert
- [ ] Plausibilitätsprüfung: Ergebnis für ein Beispiel-Einkommen gegen BMF-Tabelle oder [bmf-steuerrechner.de](https://www.bmf-steuerrechner.de) geprüft
- [ ] EXE neu gebaut und Release-ZIP erstellt

---

## 📝 Erweiterungen & Roadmap

### Geplant

1. **Weitere Jahrgänge:** Wenn BMF-Formeln verfügbar (z.B. 2027 f.)
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

1. **Steuerklassenlogik vereinfacht:** Orientierung am Grundtarif mit praxisnahen Sonderregeln (Splitting, SK5/SK6-Anpassungen)
2. **KFB-Modell:** Linear vereinfacht (50 €/KFB), nicht alle Feinheiten
3. **Keine Lohn-Grenzen:** Z.B. Mindestlohn, Gleitzone nicht berücksichtigt
4. **GUI Single-Thread:** Lange Generierungen können UI einfrieren (60+ Sek)
5. **Keine Abbruch-Option:** Laufende Generierung kann nicht unterbrochen werden

---

## 📚 Referenzen

- **BMF Einkommensteuer-Tarifformeln 2026:** [Bundesfinanzministerium](https://www.bundesfinanzministerium.de/)
- **§ 32a EStG:** Einkommensteuergesetz
- **pandas Dokumentation:** [pandas.pydata.org](https://pandas.pydata.org/)
- **Tkinter Dokumentation:** [docs.python.org](https://docs.python.org/3/library/tkinter.html)

## 🗒️ Änderungsstand

- **08.05.2026:** Dokumentation mit Implementierung abgeglichen (Tarifwerte, Steuerklassenlogik, Quellenangaben).

---

**Version:** 1.0.0  
**Stand:** 07.05.2026  
**Autor:** GoroTech  
**Lizenz:** Frei – Nutzung, Weitergabe und Anpassung ohne Einschränkungen gestattet.  
**Zielentwickler:** Python 3.8+
