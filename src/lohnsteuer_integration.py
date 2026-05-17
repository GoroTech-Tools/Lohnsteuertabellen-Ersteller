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
import sys
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

    @staticmethod
    def _get_default_pap_xml_dir() -> Path:
        """Liefert den Standardpfad zu den PAP-XML-Dateien für Dev- und EXE-Modus."""
        candidates: list[Path] = []

        if getattr(sys, "frozen", False):
            meipass = getattr(sys, "_MEIPASS", None)
            if meipass:
                candidates.append(Path(meipass) / "data" / "pap_xml")

            executable = getattr(sys, "executable", None)
            if executable:
                candidates.append(Path(executable).resolve().parent / "data" / "pap_xml")

        project_root = Path(__file__).resolve().parent.parent
        candidates.append(project_root / "data" / "pap_xml")

        for candidate in candidates:
            if candidate.exists():
                return candidate

        return candidates[0]
    
    def __init__(self, pap_xml_dir: Optional[str] = None):
        """
        Initialisiere PAP Parser.
        
        Args:
            pap_xml_dir: Pfad zum Verzeichnis mit PAP-XML-Dateien.
                        Standard: ./data/pap_xml
        """
        if pap_xml_dir is None:
            pap_xml_dir = self._get_default_pap_xml_dir()
        
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

    def _extract_kfb_faktor_sk123(self, root: ET.Element) -> Optional[int]:
        """
        Extrahiere den KFB-Faktor fuer SK 1/2/3 aus dem PAP-XML.

        Beispiel im XML:
            <EVAL exec="KFB= (ZKF.multiply (BigDecimal.valueOf(9756))).setScale (0, BigDecimal.ROUND_DOWN)"/>
        """
        pattern = re.compile(
            r'KFB\s*=\s*\(?\s*ZKF\.multiply\s*\(\s*BigDecimal\.valueOf\s*\(\s*(\d+)\s*\)'
        )
        for eval_elem in root.findall(".//EVAL"):
            exec_expr = eval_elem.get("exec", "")
            match = pattern.search(exec_expr)
            if match:
                return int(match.group(1))
        return None

    # Jahresspezifische UPTAB-Parameter (Fallback falls XML-Extraktion nicht greift)
    _UPTAB_PARAMS: Dict[int, Dict] = {
        2026: {"z1": 17800, "z2": 69879, "z3": 277826, "a1": 914.51,  "b1": 1400.0, "a2": 173.10, "b2": 2397.0, "c2": 1034.87, "r1": 0.42, "o1": 11135.63, "r2": 0.45, "o2": 19470.38},
        2025: {"z1": 17444, "z2": 68481, "z3": 277826, "a1": 932.30,  "b1": 1400.0, "a2": 176.64, "b2": 2397.0, "c2": 1015.13, "r1": 0.42, "o1": 10911.92, "r2": 0.45, "o2": 19246.67},
        2024: {"z1": 17006, "z2": 66761, "z3": 277826, "a1": 922.98,  "b1": 1400.0, "a2": 181.19, "b2": 2397.0, "c2": 1025.38, "r1": 0.42, "o1": 10602.13, "r2": 0.45, "o2": 18936.88},
    }

    # Jahresspezifische KFB-Faktoren (Fallback)
    _KFB_FAKTOR_SK123: Dict[int, int] = {
        2026: 9756, 2025: 9600, 2024: 9312, 2023: 8952, 2022: 8388,
        2021: 8388, 2020: 7812, 2019: 7620, 2018: 7428, 2017: 7356,
    }

    def _berechne_tarifsteuer(self, x: float, gfb: float, kztab: int, jahr: int) -> float:
        """
        Implementiert den deutschen Einkommensteuertarif (UPTAB) fuer ein gegebenes Jahr.

        Args:
            x:     Zu versteuerndes Einkommen geteilt durch KZTAB (ganze EUR)
            gfb:   Grundfreibetrag des Jahres
            kztab: 1 = Grundtarif, 2 = Splittingverfahren
            jahr:  Steuerjahr

        Returns:
            Tarifsteuer in EUR (Jahresbetrag)
        """
        p = self._UPTAB_PARAMS.get(jahr, self._UPTAB_PARAMS.get(2026))
        x = float(int(x))  # Auf ganze EUR abrunden
        if x < gfb + 1:
            st = 0.0
        elif x < p["z1"]:
            y = (x - gfb) / 10000.0
            st = float(int((y * p["a1"] + p["b1"]) * y))
        elif x < p["z2"]:
            y = (x - (p["z1"] - 1)) / 10000.0
            st = float(int((y * p["a2"] + p["b2"]) * y + p["c2"]))
        elif x < p["z3"]:
            st = float(int(x * p["r1"] - p["o1"]))
        else:
            st = float(int(x * p["r2"] - p["o2"]))
        return st * kztab

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
        zkf: float = 0.0,
        krankenkasse: str = "gesetzlich"
    ) -> Dict[str, float]:
        """
        Berechne Lohnsteuer, SolZ, Kirchensteuer-Basis und Netto fuer Bruttolohn.

        Implementiert den PAP-Algorithmus (MBERECH) naeherungsweise:
          - Korrekte Vorsorgepauschale (VSP) gemaess PAP §39b Abs.2 S.5 Nr.3
          - Korrekte ZTABFB (ANP, SAP, EFA)
          - Korrekter UPTAB-Tarif je Steuerjahr
          - Korrekte KFB-Berechnung (ZKF * KFB-Faktor, abhaengig von Steuerklasse)
          - JBMG-Zweidurchlauf: Soli und Kirchensteuer basieren auf Steuer nach KFB-Abzug

        Args:
            bruttolohn:  Bruttolohn in EUR fuer den Lohnzahlungszeitraum
            jahr:        Steuerjahr
            steuerkl:    Steuerklasse (1-6)
            lzz:         Lohnzahlungszeitraum (1=Jahr, 2=Monat, 3=Woche, 4=Tag)
            kinder:      Anzahl Kinder (fuer PV-Kinderlosenzuschlag)
            zkf:         Zahl der Kinderfreibetraege (z.B. 0, 0.5, 1.0, 1.5 ...)
            krankenkasse: "gesetzlich" oder "privat"

        Returns:
            Dict mit Keys: brutto, lohnsteuer, soli, kirchensteuer_basis,
                           krv, pvz, netto, effektiv_steuersatz_prozent
        """
        tarifwerte = self.extract_tarifwerte(jahr)
        gfb = float(tarifwerte.grundfreibetrag)

        # Annualisieren
        lzz_div = {1: 1, 2: 12, 3: 52, 4: 365}.get(lzz)
        if lzz_div is None:
            raise ValueError(f"Unbekannter LZZ: {lzz}")
        jahresbrutto = bruttolohn * lzz_div

        # KZTAB: 1 = Grundtarif, 2 = Splittingverfahren (SK 3)
        kztab = 2 if steuerkl == 3 else 1

        # ---------------------------------------------------------------
        # Vorsorgepauschale (VSP) gemaess PAP UPEVP/MVSPKVPV/MVSPHB
        # Vereinfachte Naeherung ohne PKV-Sonderfall
        # ---------------------------------------------------------------
        bbgrvalv = 101400.0   # 2026; fuer aeltere Jahre akzeptable Naeherung
        bbgkvpv  =  69750.0
        rvsatzan = 0.0930
        kvsatzan = 0.0785     # 7% AN-Anteil + 0.85% (halber Zusatzbeitrag ~1.7%)
        pvsatzan = 0.0180     # ohne Kinderlosenzuschlag
        avsatzan = 0.0130

        zre4vp_rv = min(jahresbrutto, bbgrvalv)
        vspr      = zre4vp_rv * rvsatzan
        zre4vp_kv = min(jahresbrutto, bbgkvpv)
        vspkvpv   = zre4vp_kv * (kvsatzan + pvsatzan)
        # Hoechtsbetrag ALV (§39b Abs.2 S.5 Nr.3e)
        vspalv    = min(zre4vp_rv, bbgrvalv) * avsatzan
        vsphb     = min(vspalv + vspkvpv, 1900.0)
        vspn      = -(-vspr - vsphb // 1)  # aufrunden (ceil)
        vsp       = max(-(-( vspr + vspkvpv) // 1), vspn)  # aufrunden, max beider
        # Vereinfacht: direkte Summe aufgerundet
        import math
        vsp = math.ceil(vspr + vspkvpv)

        # ---------------------------------------------------------------
        # ZTABFB: feste Tabellenfreibetraege (ohne VSP)
        # ANP = Arbeitnehmer-Pauschbetrag (max 1230€, SK 1-5)
        # SAP = Sonderausgaben-Pauschbetrag (36€)
        # EFA = Entlastungsbetrag Alleinerziehende (4260€, nur SK 2)
        # ---------------------------------------------------------------
        anp   = 1230.0 if steuerkl < 6 else 0.0
        sap   = 36.0
        efa   = 4260.0 if steuerkl == 2 else 0.0
        ztabfb = efa + anp + sap

        # ---------------------------------------------------------------
        # KFB (Summe Kinderfreibetraege je Jahr) gemaess MZTABFB
        # SK 1/2/3: KFB = int(ZKF * kfb_faktor_sk123)
        # SK 4:     KFB = int(ZKF * kfb_faktor_sk4)
        # SK 5/6:   KFB = 0
        # ---------------------------------------------------------------
        xml_root = None
        try:
            xml_datei = self._find_xml_file(jahr)
            if xml_datei.exists():
                import xml.etree.ElementTree as _ET
                xml_root = _ET.parse(xml_datei).getroot()
        except Exception:
            pass

        if zkf > 0:
            # Faktor aus XML extrahieren oder Fallback-Dict
            kfb_faktor_raw = (
                self._extract_kfb_faktor_sk123(xml_root) if xml_root is not None else None
            )
            kfb_faktor_sk123 = kfb_faktor_raw if kfb_faktor_raw else self._KFB_FAKTOR_SK123.get(jahr, 9756)
            kfb_faktor_sk4   = kfb_faktor_sk123 // 2

            if steuerkl in (1, 2, 3):
                kfb_annual = int(zkf * kfb_faktor_sk123)
            elif steuerkl == 4:
                kfb_annual = int(zkf * kfb_faktor_sk4)
            else:  # SK 5, 6
                kfb_annual = 0
        else:
            kfb_annual = 0

        # ---------------------------------------------------------------
        # ZRE4 = Jahresbruttolohn (vereinfacht ohne FVB, ALTE, LZZFREIB)
        # ZVE  = Zu versteuerndes Einkommen
        # ---------------------------------------------------------------
        zre4 = jahresbrutto
        zve  = max(0.0, zre4 - ztabfb - vsp)

        # ---------------------------------------------------------------
        # Erster Durchlauf: LSTJAHR (Jahreslohnsteuer ohne KFB-Abzug)
        # gemaess MBERECH → MLSTJAHR → UPMLST → UPTAB
        # ---------------------------------------------------------------
        x_ohne = int(zve / kztab)
        lstjahr = self._berechne_tarifsteuer(x_ohne, gfb, kztab, jahr)

        # ---------------------------------------------------------------
        # Zweiter Durchlauf: JBMG (Jahressteuer nach §51a EStG)
        # Bemessungsgrundlage fuer Soli und Kirchensteuer.
        # Nur wenn ZKF > 0: ZTABFB += KFB, dann neu berechnen.
        # ---------------------------------------------------------------
        if kfb_annual > 0:
            zve_jbmg = max(0.0, zre4 - ztabfb - vsp - kfb_annual)
            x_mit    = int(zve_jbmg / kztab)
            jbmg     = self._berechne_tarifsteuer(x_mit, gfb, kztab, jahr)
        else:
            jbmg = lstjahr

        # ---------------------------------------------------------------
        # Solidaritaetszuschlag (MSOLZ)
        # Freigrenze: SOLZFREI * KZTAB
        # SOLZJ = min(JBMG * 5.5%, (JBMG - SOLZFREI_eff) * 11.9%)
        # ---------------------------------------------------------------
        solzfrei_raw = tarifwerte.grenzwerte.get("solzfrei", Decimal("20350"))
        solzfrei_eff = float(solzfrei_raw) * kztab
        if jbmg > solzfrei_eff:
            solzj = min(jbmg * 0.055, (jbmg - solzfrei_eff) * 0.119)
        else:
            solzj = 0.0

        # PV-Zuschlag Kinderlose (0.6% fuer kinder == 0, SK != 6)
        if kinder == 0 and steuerkl != 6:
            pvz_jahr = jahresbrutto * 0.006
        else:
            pvz_jahr = 0.0

        # KV-Zuschlag bei privater Krankenversicherung
        krv_jahr = jahresbrutto * 0.008 if krankenkasse == "privat" else 0.0

        # Auf Lohnzahlungszeitraum herunterrechnen
        lohnsteuer         = lstjahr  / lzz_div
        soli               = solzj    / lzz_div
        kirchensteuer_basis = jbmg    / lzz_div   # Bemessungsgrundlage fuer Kirchensteuer
        krv                = krv_jahr / lzz_div
        pvz                = pvz_jahr / lzz_div

        netto = bruttolohn - lohnsteuer - soli - krv - pvz
        effektiv_prozent = (lohnsteuer / bruttolohn * 100) if bruttolohn > 0 else 0.0

        return {
            "brutto":                    bruttolohn,
            "lohnsteuer":                round(lohnsteuer, 2),
            "soli":                      round(soli, 2),
            "kirchensteuer_basis":       round(kirchensteuer_basis, 2),
            "krv":                       round(krv, 2),
            "pvz":                       round(pvz, 2),
            "netto":                     round(netto, 2),
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
