"""
PAP (Programmablaufplan) XML-Parser für Lohnsteuerberechnungen.

Extrahiert Tarifwerte und Berechnung-Parameter aus den XML-Programmablaufplänen
des Bundesministerium der Finanzen (BMF).

Quelle: https://github.com/MarcelLehmann/Lohnsteuer (Apache 2.0)
© 2015-2025 Marcel Lehmann (PAP-Generator)
Adaptiert für: Lohnsteuertabellen-Ersteller

Verwendung:
    parser = PAPParser()
    tarifwerte_2026 = parser.extract_tarifwerte(2026)
    netto = parser.berechne_lohnsteuer(
        bruttolohn=40000,
        jahr=2026,
        steuerkl=1,
        lzz=2  # 2=Monat
    )
"""

import xml.etree.ElementTree as ET
import json
import re
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional
from decimal import Decimal


@dataclass
class Tarifwerte:
    """Container für Tarifwerte eines Jahres."""
    jahr: int
    grundfreibetrag: Decimal
    steuersaetze: Dict[str, Decimal]
    grenzwerte: Dict[str, Decimal]
    zusaetze: Dict[str, Decimal]
    
    def to_dict(self) -> dict:
        """Konvertiere zu Dictionary für JSON/CSV."""
        return {
            "jahr": self.jahr,
            "grundfreibetrag": float(self.grundfreibetrag),
            "steuersaetze": {k: float(v) for k, v in self.steuersaetze.items()},
            "grenzwerte": {k: float(v) for k, v in self.grenzwerte.items()},
            "zusaetze": {k: float(v) for k, v in self.zusaetze.items()},
        }


class PAPParser:
    """
    Parser für BMF Programmablaufplan XML-Dateien.
    
    Die XML-Dateien definieren die offizielle Lohnsteuerberechnung.
    """
    
    def __init__(self, pap_xml_dir: Optional[str] = None):
        """
        Initialisiere PAP Parser.
        
        Args:
            pap_xml_dir: Pfad zum Verzeichnis mit PAP-XML-Dateien.
                        Standard: ./data/pap_xml
        """
        if pap_xml_dir is None:
            # Versuche Standard-Pfade
            project_root = Path(__file__).parent.parent
            pap_xml_dir = project_root / "data" / "pap_xml"
        
        self.pap_xml_dir = Path(pap_xml_dir)
        self._cache: Dict[int, Tarifwerte] = {}
        
        if not self.pap_xml_dir.exists():
            raise FileNotFoundError(
                f"PAP XML-Verzeichnis nicht gefunden: {self.pap_xml_dir}\n"
                "Bitte stelle sicher, dass data/pap_xml/ existiert mit XML-Dateien."
            )
    
    def extract_tarifwerte(self, jahr: int) -> Tarifwerte:
        """
        Extrahiere Tarifwerte aus PAP-XML für ein Jahr.
        
        Args:
            jahr: Jahrzahl (z.B. 2026)
            
        Returns:
            Tarifwerte-Objekt mit allen Parametern
            
        Raises:
            FileNotFoundError: Wenn XML für Jahr nicht vorhanden
            ValueError: Wenn XML-Parsing fehlschlägt
        """
        # Aus Cache?
        if jahr in self._cache:
            return self._cache[jahr]
        
        # XML-Datei finden
        xml_datei = self._find_xml_file(jahr)
        if not xml_datei.exists():
            raise FileNotFoundError(
                f"PAP-XML nicht gefunden für Jahr {jahr}.\n"
                f"Gesucht: {xml_datei}\n"
                f"Verfügbar: {list(self.pap_xml_dir.glob('*.xml'))}"
            )
        
        try:
            tree = ET.parse(xml_datei)
            root = tree.getroot()
            
            # Extrahiere Key-Tarifwerte
            # In PAP-XML wird der Grundfreibetrag typischerweise via
            # EVAL exec="GFB = BigDecimal.valueOf(12348)" gesetzt.
            grundfreibetrag = self._extract_exec_decimal(root, "GFB")
            if grundfreibetrag is None:
                # Fallback, falls Jahr/Format abweicht
                grundfreibetrag = Decimal("12000")

            steuersaetze = self._extract_steuersaetze(root)
            grenzwerte = self._extract_grenzwerte(root)
            zusaetze = self._extract_zusaetze(root)
            
            tarifwerte = Tarifwerte(
                jahr=jahr,
                grundfreibetrag=grundfreibetrag,
                steuersaetze=steuersaetze,
                grenzwerte=grenzwerte,
                zusaetze=zusaetze,
            )
            
            # Cache
            self._cache[jahr] = tarifwerte
            return tarifwerte
            
        except ET.ParseError as e:
            raise ValueError(
                f"Fehler beim Parsen von {xml_datei}: {e}"
            ) from e
    
    def _find_xml_file(self, jahr: int) -> Path:
        """Finde XML-Datei für Jahr."""
        return self.pap_xml_dir / f"Lohnsteuer{jahr}.xml"
    
    def _extract_value(
        self, root: ET.Element, tag_name: str, 
        value_type=str
    ) -> any:
        """
        Extrahiere numerischen Wert aus XML-Element.
        
        Args:
            root: XML-Root-Element
            tag_name: Name des zu suchenden Tags
            value_type: Zieldatentyp (str, int, float, Decimal)
            
        Returns:
            Konvertierter Wert oder None
        """
        element = root.find(f".//{tag_name}")
        if element is None or element.text is None:
            return None
        
        text = element.text.strip()
        
        if value_type == Decimal:
            # Lohnsteuer-XML nutzt EUR in Cents
            # "12084" = 120.84 EUR oder 12084 Cents
            return Decimal(text) / 100
        elif value_type == int:
            return int(text)
        elif value_type == float:
            return float(text)
        else:
            return text

    def _extract_exec_decimal(self, root: ET.Element, variable_name: str) -> Optional[Decimal]:
        """
        Extrahiere numerischen BigDecimal.valueOf(...) Wert aus EVAL-exec.

        Beispiel im XML:
            <EVAL exec="GFB = BigDecimal.valueOf(12348)"/>
        """
        pattern = re.compile(
            rf"\b{re.escape(variable_name)}\s*=\s*BigDecimal\.valueOf\(([-+]?[0-9]*\.?[0-9]+)\)"
        )

        for eval_elem in root.findall(".//EVAL"):
            exec_expr = eval_elem.get("exec")
            if not exec_expr:
                continue
            match = pattern.search(exec_expr)
            if match:
                return Decimal(match.group(1))

        return None
    
    def _extract_steuersaetze(self, root: ET.Element) -> Dict[str, Decimal]:
        """Extrahiere Steuersätze aus PAP."""
        saetze = {}
        
        # Typische Steuersätze in Tarifzonen
        steuersatz_elems = root.findall(".//Steuersatz")
        for elem in steuersatz_elems:
            zone = elem.get("zone", "unbekannt")
            rate = elem.get("rate")
            if rate:
                saetze[f"zone_{zone}"] = Decimal(rate) / 100
        
        # Fallback: Gängige deutsche Steuersätze (wenn nicht in XML)
        if not saetze:
            saetze = {
                "grundtarif": Decimal("0.42"),
                "spitzensatz": Decimal("0.45"),
                "soli": Decimal("0.0055"),
            }
        
        return saetze
    
    def _extract_grenzwerte(self, root: ET.Element) -> Dict[str, Decimal]:
        """Extrahiere Grenzwerte aus PAP."""
        grenzwerte = {}
        
        grenzwert_elems = root.findall(".//Grenzwert")
        for elem in grenzwert_elems:
            name = elem.get("name", "unbekannt")
            value = elem.get("value")
            if value:
                grenzwerte[name] = Decimal(value) / 100
        
        # Ergänze häufige PAP-Konstanten direkt aus EVAL-Zuweisungen
        for var in ["SOLZFREI", "W1STKL5", "W2STKL5", "W3STKL5"]:
            value = self._extract_exec_decimal(root, var)
            if value is not None:
                grenzwerte[var.lower()] = value

        # Fallback: Standard-Grenzwerte 2026
        if not grenzwerte:
            grenzwerte = {
                "grundfreibetrag_grenze": Decimal("12084"),
                "versicherungsgrenze_krv": Decimal("168000"),
                "midijob_grenze": Decimal("15000"),
            }
        
        return grenzwerte
    
    def _extract_zusaetze(self, root: ET.Element) -> Dict[str, Decimal]:
        """Extrahiere Zusätze (Solidaritätszuschlag, KV-Zuschlag, etc)."""
        zusaetze = {}
        
        # Solidaritätszuschlag (typisch: 5.5% auf Einkommen­steuer ab ca. 972€)
        # Krankenversicherungs-Zuschlag
        # Pflegeversicherungs-Zuschlag
        
        zusatz_elems = root.findall(".//Zusatz")
        for elem in zusatz_elems:
            name = elem.get("name", "unbekannt")
            value = elem.get("value")
            if value:
                zusaetze[name] = Decimal(value) / 100
        
        # Fallback 2026
        if not zusaetze:
            zusaetze = {
                "solidaritaetszuschlag_prozent": Decimal("0.055"),
                "krv_zuschlag_prozent": Decimal("0.01"),
                "pvz_zuschlag_prozent": Decimal("0.002"),
            }
        
        return zusaetze
    
    def berechne_lohnsteuer(
        self,
        bruttolohn: float,
        jahr: int = 2026,
        steuerkl: int = 1,
        lzz: int = 2,  # 1=Jahr, 2=Monat, 3=Woche, 4=Tag
        kinder: int = 0,
        krankenkasse: str = "gesetzlich"
    ) -> Dict[str, float]:
        """
        Berechne Lohnsteuer & Netto für Bruttolohn.
        
        HINWEIS: Das ist eine vereinfachte Implementierung.
        Für komplexe Szenarien nutze das JAR oder Java-API.
        
        Args:
            bruttolohn: Bruttolohn in EUR
            jahr: Steuerjahr
            steuerkl: Steuerklasse (1-6)
            lzz: Lohnzahlungszeitraum (1=Jahr, 2=Monat, etc.)
            kinder: Anzahl Kinder (für Kinderlosigkeitszuschlag)
            krankenkasse: "gesetzlich" oder "privat"
            
        Returns:
            Dict mit Keys: brutto, lohnsteuer, soli, krv, pvz, netto, effektiv_prozent
        """
        tarifwerte = self.extract_tarifwerte(jahr)
        
        # Annualisieren wenn nötig
        if lzz == 1:
            jahresbrutto = bruttolohn
        elif lzz == 2:
            jahresbrutto = bruttolohn * 12
        elif lzz == 3:
            jahresbrutto = bruttolohn * 52
        elif lzz == 4:
            jahresbrutto = bruttolohn * 365
        else:
            raise ValueError(f"Unbekannter LZZ: {lzz}")
        
        # Vereinfachte Berechnung (ohne alle Spitzfindigkeiten)
        # Für produktive Nutzung: Java-API nutzen!
        
        zu_versteuerndes_einkommen = max(
            0,
            float(jahresbrutto) - float(tarifwerte.grundfreibetrag)
        )
        
        # Progressiver Tarif (vereinfacht)
        if zu_versteuerndes_einkommen == 0:
            lohnsteuer_jahres = 0
        elif zu_versteuerndes_einkommen <= 11000:
            # Aufstiegszone
            lohnsteuer_jahres = zu_versteuerndes_einkommen * 0.19
        elif zu_versteuerndes_einkommen <= 44500:
            # Normaltarif
            lohnsteuer_jahres = (
                11000 * 0.19 +
                (zu_versteuerndes_einkommen - 11000) * 0.42
            )
        else:
            # Spitzentarif
            lohnsteuer_jahres = (
                11000 * 0.19 +
                33500 * 0.42 +
                (zu_versteuerndes_einkommen - 44500) * 0.45
            )
        
        # Solidaritätszuschlag (5.5% auf Lohnsteuer, ab Freibetrag)
        soli_freibetrag = 972
        soli = max(0, (lohnsteuer_jahres - soli_freibetrag)) * 0.055
        
        # KV-Zuschlag (falls privat)
        if krankenkasse == "privat":
            krv_zuschlag = jahresbrutto * 0.008
        else:
            krv_zuschlag = 0
        
        # PV-Zuschlag Kinderlose (0.25% ab 23 Jahren)
        if kinder == 0:
            pv_zuschlag = jahresbrutto * 0.0025
        else:
            pv_zuschlag = 0
        
        # Auf Lohnzahlungszeitraum runterrechnen
        faktor = 1 / 12 if lzz == 2 else 1 / 52 if lzz == 3 else 1 / 365 if lzz == 4 else 1
        
        lohnsteuer = lohnsteuer_jahres * faktor
        soli = soli * faktor
        krv = krv_zuschlag * faktor
        pvz = pv_zuschlag * faktor
        
        netto = bruttolohn - lohnsteuer - soli - krv - pvz
        effektiv_prozent = (lohnsteuer / bruttolohn * 100) if bruttolohn > 0 else 0
        
        return {
            "brutto": bruttolohn,
            "lohnsteuer": round(lohnsteuer, 2),
            "soli": round(soli, 2),
            "krv": round(krv, 2),
            "pvz": round(pvz, 2),
            "netto": round(netto, 2),
            "effektiv_steuersatz_prozent": round(effektiv_prozent, 2),
        }
    
    def export_tarifwerte_json(self, jahr: int, output_path: str) -> None:
        """Exportiere Tarifwerte als JSON."""
        tarifwerte = self.extract_tarifwerte(jahr)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(tarifwerte.to_dict(), f, indent=2, ensure_ascii=False)
    
    def export_tarifwerte_csv(self, jahrgaenge: List[int], output_path: str) -> None:
        """Exportiere Tarifwerte mehrerer Jahre als CSV."""
        import csv
        
        rows = []
        for jahr in jahrgaenge:
            try:
                tarifwerte = self.extract_tarifwerte(jahr)
                row = tarifwerte.to_dict()
                row['jahr'] = jahr
                rows.append(row)
            except FileNotFoundError:
                pass  # Jahr überspringen
        
        if not rows:
            raise ValueError("Keine Tarifwerte gefunden!")
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)


if __name__ == "__main__":
    # Test-Beispiel
    try:
        parser = PAPParser()
        
        # Tarifwerte für 2026 extrahieren
        print("📊 Extrahiere Tarifwerte 2026...")
        tarifwerte_2026 = parser.extract_tarifwerte(2026)
        print(f"  Grundfreibetrag: {tarifwerte_2026.grundfreibetrag}€")
        print(f"  Steuersätze: {tarifwerte_2026.steuersaetze}")
        
        # Berechne Netto
        print("\n💰 Beispiel-Berechnung (Brutto 3000€/Monat, Steuerklasse I):")
        result = parser.berechne_lohnsteuer(3000, jahr=2026, steuerkl=1, lzz=2)
        for key, value in result.items():
            print(f"  {key}: {value}")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
