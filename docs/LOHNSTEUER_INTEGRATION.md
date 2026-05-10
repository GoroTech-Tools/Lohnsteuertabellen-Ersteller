# Analyse: Lohnsteuer-2026_1 Integration in Lohnsteuertabellen-Ersteller

## Projektübersicht

**Quelle:** `D:\Lohnsteuer-2026_1` (Java Lohnsteuer-Rechner, © 2015-2025 Marcel Lehmann)
**Lizenz:** Apache 2.0 ✅ (kompatibel, Attribution erforderlich)
**Basis:** Offizielle Programmablaufpläne (PAP) des Bundesministerium der Finanzen (BMF)

---

## Relevante Komponenten

### 1. lohnsteuer.jar (Direkt nutzbar)

- **Pfad:** `LohnPapGenerator/lohnsteuer.jar`
- **Inhalt:** Kompilierte Java-Klassen für Lohnsteuerberechnung
- **Jahrgänge:** 2006-2026
- **Verwendung:**
  - Via JNI in Python laden
  - Oder als Sub-Process aufrufen
  - Oder Java-API studieren und in Python nachbilden

### 2. Java-Quellcode (Referenz/Logik-Vorlage)

- **Verzeichnis:** `LohnPapGenerator/src/de/powerproject/lohnpap/pap/`
- **Dateien:** `Lohnsteuer.java`, `Lohnsteuer2026.java`, ... `Lohnsteuer2006.java`
- **Inhalt:**
  - Setter-Methoden für Input-Variablen (z.B. `setJre4()` = Jahresarbeitslohn)
  - Berechnungslogik (`main()`)
  - Getter-Methoden für Output (z.B. `getLstlzz()` = Lohnsteuer in Cents)
  - Inline-Kommentare zum PAP-Standard
- **Nutzung für Tabellen-Generator:**
  - Template für Python-Ableitung
  - Verständnis der Ein/Ausgabe-Variablen
  - Validierungsreferenz

### 3. XML PAP-Dateien (Dokumentation)

- **Verzeichnis:** `LohnPapGenerator/src/de/powerproject/lohnpap/xml/`
- **Dateien:** `Lohnsteuer2026.xml`, `Lohnsteuer2025.xml`, ...
- **Inhalt:**
  - Programmablaufplan als strukturiertes XML
  - Berechnungsschritte, Formeln, Konstanten pro Jahr
  - Offizielle Basis für Generator
- **Nutzung:**
  - Daten-Extraktion (Steuersätze, Freibeträge, Grenzwerte pro Jahr)
  - Automatisierte Tabellenerzeugung aus XML

### 4. Interface-Definition (API-Standard)

- **Datei:** `LohnsteuerInterface.java`
- **Nutzen:** Standardisierte Input/Output-Variablen über alle Jahre

---

## Integration-Optionen für Lohnsteuertabellen-Ersteller

### Option A: JAR direkt nutzen (schnellste)

```python
# In Python über JPype oder Jython
from jpype import *

# JAR laden
addClassPath("LohnPapGenerator/lohnsteuer.jar")
Lohnsteuer = JClass("de.powerproject.lohnpap.pap.Lohnsteuer2026")

# Instanz erstellen
rechner = Lohnsteuer.getInstance()

# Eingaben
rechner.setJre4(40000 * 100)  # 40.000€ in Cents
rechner.setLzz(1)             # Lohnzahlungszeitraum (1=Monat)
rechner.main()                # Berechnung

# Ausgabe
steuer_cents = rechner.getLstlzz()  # Lohnsteuer in Cents
```

**Vorteil:** Sofort lauffähig, 100% Korrektheit  
**Nachteil:** Java-Runtime notwendig, zusätzliche Abhängigkeit

---

### Option B: Python-Implementierung (empfohlen für Portabilität)

```python
# XML parsen + PAP-Logik in Python übersetzen
import xml.etree.ElementTree as ET
from dataclasses import dataclass

@dataclass
class LohnsteuerTarifJahr:
    jahr: int
    grundfreibetrag: float
    steuersaetze: dict  # z.B. {0.19: "19%"}
    spitzensteuersatz: float
    # ... weitere PAP-Konstanten
    
    @classmethod
    def from_xml(cls, xml_pfad):
        """Extrahiere Tarifwerte aus Lohnsteuer2026.xml"""
        tree = ET.parse(xml_pfad)
        root = tree.getroot()
        # Parsing-Logik ...
        return cls(...)

def berechne_lohnsteuer_2026(bruttolohn: float) -> dict:
    """Lohnsteuerberechnung basierend auf PAP-Logik"""
    # Implementierung der PAP-Formeln
    return {
        "jahressteuer": ...
        "monatssteuer": ...
        "netto": ...
    }
```

**Vorteil:** Keine Java-Abhängigkeit, leicht zu debuggen, flexibel erweiterbar  
**Nachteil:** Manuelle Umsetzung pro Jahr

---

### Option C: Hybrid (Best Practice)

1. XML extrahieren → Python-Datenstrukturen erzeugen
2. JAR als Validierungs-Fallback für komplexe Fälle
3. Generierte Tabellen mit beiden Quellen kreuzvalidieren

---

## Konkrete Umsetzungs-Schritte

### Schritt 1: Datei-Struktur in Lohnsteuertabellen-Ersteller

```text
src/
  lohnsteuer_integration/
    __init__.py
    pap_parser.py          # XML → Datenstruktur
    berechnungen.py        # Geschäftslogik
    java_bridge.py         # JAR-Integration (optional)
  
docs/
  LOHNSTEUER_SOURCE.md     # Diese Dokumentation
  
data/
  lohnsteuer_pap/          # Kopie der XML-Dateien
    lohnsteuer_2026.xml
    lohnsteuer_2025.xml
    ...
```

### Schritt 2: XML-Extraktion

Beispiel aus `Lohnsteuer2026.xml`:

```xml
<Lohnsteuer>
  <Berechnung>
    <Grundfreibetrag>12084</Grundfreibetrag>
    <Spitzensteuersatz>45.0</Spitzensteuersatz>
    <Steuertarif> ... </Steuertarif>
  </Berechnung>
</Lohnsteuer>
```

→ Python-Dict erzeugen für Tabellenberechnung

### Schritt 3: Tabellen-Generator aktualisieren

```python
def generate_lohnsteuer_table(jahr: int, bruttospanne: list) -> DataFrame:
    """Generiere Lohnsteuer-Tabelle aus PAP-Logik"""
    pap = PAP_Parser.load_xml(f"data/lohnsteuer_pap/lohnsteuer_{jahr}.xml")
    results = []
    
    for brutto in bruttospanne:
        steuer = berechne_lohnsteuer(brutto, pap)
        results.append({
            "bruttolohn": brutto,
            "lohnsteuer": steuer["jahressteuer"],
            "netto": brutto - steuer["jahressteuer"],
            "steuersatz": steuer["effektiv_prozent"]
        })
    
    return pd.DataFrame(results)
```

---

## Lizenzkompliance

**Erforderlich:**

- ✅ Apache 2.0 License-Text einbinden (bereits vorhanden in LICENSE.md)
- ✅ Copyright-Hinweis: "© 2015-2025 Marcel Lehmann (Apache 2.0)"
- ✅ Quellenangabe: <https://github.com/MarcelLehmann/Lohnsteuer> (falls verlinkt)

**Einfach zu erfüllen mit Datei `DEPENDENCIES.md`:**

```markdown
## Abhängigkeiten & Lizenzen

### Lohnsteuer-Rechner
- **Projekt:** Lohnsteuer (PAP-Generator)
- **Autor:** Marcel Lehmann
- **Quelle:** https://github.com/MarcelLehmann/Lohnsteuer
- **Lizenz:** Apache License 2.0
- **Verwendung:** Referenz-Implementierung für Lohnsteuerberechnungen und PAP-Daten
```

---

## Empfehlung

**Sofortmaßnahmen:**

1. ✅ **XML-Dateien kopieren** → `src/data/lohnsteuer_pap/`
2. ✅ **Lizenz dokumentieren** → `DEPENDENCIES.md` erweitern
3. ✅ **PAP-Parser erstellen** → `src/lohnsteuer_integration/pap_parser.py`
4. ✅ **Tarifwerte extrahieren** → CSV/JSON für schnelle Tabellenerzeugung
5. ✅ **Validierungs-Tests** → JAR optional nutzen für Kreuzvalidierung

---

## Weitere Ressourcen

- [Offizielle PAP vom BMF](https://www.bmf-steuerrechner.de/interface/programmablauf.xhtml)
- [GitHub: MarcelLehmann/Lohnsteuer](https://github.com/MarcelLehmann/Lohnsteuer)
- [PAP 2026 PDF (BMF)](https://www.bundesfinanzministerium.de/Content/DE/Downloads/...)

---

**Analysedatum:** 10. Mai 2026  
**Status:** Bereit zur Integration  
**Komplexität:** Mittel (PAP-Logik ist komplex, aber gut dokumentiert)
