# -*- coding: utf-8 -*-
"""
Generiert eine Lohnsteuertabelle für 2026 basierend auf den gültigen Tarifparametern.
Berechnet Lohnsteuer, Solidaritätszuschlag und Kirchensteuer für alle Steuerklassen.

Nutzung:
    python generate_2026_tax_table.py -o "Lohnsteuer_2026_West.xlsx"

Parameter:
    - Einkommensbereiche: 1000 - 10000€
    - Steuerklassen: 1-6
    - KFB-Werte: 0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4
    - Kirchensteuersatz: 9%
    - Region: West (monatliche Tabelle)
    - Schrittweite: 5€
"""

import argparse
import math
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import sys

# ===================== 2026 TARIFPARAMETER =====================
# Quelle: § 32a Abs. 1 EStG, Fassung ab Veranlagungszeitraum 2026
TAX_PARAMS_2026 = {
    # Tarifzonen § 32a EStG 2026
    "grundfreibetrag":  12348,   # Zone 1 bis hier: 0 € Steuer
    "grenze_zone2":     17799,   # Zone 2: 12.349–17.799 €
    "grenze_zone3":     69878,   # Zone 3: 17.800–69.878 €
    "grenze_zone4":    277825,   # Zone 4: 69.879–277.825 €
                                 # Zone 5: ab 277.826 €

    # Zone 2: (914,51 · y + 1.400) · y
    "zone2_a":   914.51,
    "zone2_b":  1400.0,

    # Zone 3: (173,10 · z + 2.397) · z + 1.034,87
    "zone3_a":   173.10,
    "zone3_b":  2397.0,
    "zone3_T1": 1034.87,

    # Zone 4: 0,42 · x − 11.135,63
    "zone4_rate":    0.42,
    "zone4_offset": 11135.63,

    # Zone 5: 0,45 · x − 19.470,38
    "zone5_rate":    0.45,
    "zone5_offset": 19470.38,

    # Solidaritätszuschlag (§ 4 SolZG 1995)
    "solidarity_rate":          0.055,   # 5,5 % der Lohnsteuer
    "solidarity_milderung":     0.119,   # Milderungszone: max. 11,9 % des Übersteigungsbetrags
    # Freigrenze § 3 Abs. 3 SolZG 1995 (Jahres-Lohnsteuer)
    "solz_freigrenze_einzel":  20350,   # SK I, II, IV, V, VI
    "solz_freigrenze_splitting": 40700,  # SK III (Ehegattensplitting)

    # Pauschbeträge für Arbeitnehmer
    "arbeitnehmer_pauschbetrag":        1230,  # § 9a Satz 1 Nr. 1a EStG
    "sonderausgaben_pauschbetrag":        36,  # § 10c EStG
    "entlastungsbetrag_alleinerziehend": 4260,  # § 24b EStG (SK 2)

    # Sozialversicherungs-Beitragssätze (Arbeitnehmeranteil, West 2026)
    "rv_an_satz":  0.0930,   # Rentenversicherung 9,3 %
    "kv_an_satz":  0.0815,   # Krankenversicherung inkl. Zusatzbeitrag ~8,15 %
    "pv_an_satz":  0.0180,   # Pflegeversicherung 1,8 %
    "bbg_rv":     89400,     # Beitragsbemessungsgrenze RV
    "bbg_kv":     66150,     # Beitragsbemessungsgrenze KV/PV
}

KFB_VALUES = [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4]

# ===================== BERECHNUNGSFUNKTIONEN =====================

def _grundtarif_2026(zvE: float) -> float:
    """§ 32a Abs. 1 EStG 2026 – Grundtarif (Grundfreibetrag bereits enthalten)."""
    p = TAX_PARAMS_2026
    zvE = int(zvE)  # auf vollen Euro abrunden
    if zvE <= p["grundfreibetrag"]:
        return 0.0
    elif zvE <= p["grenze_zone2"]:
        y = (zvE - p["grundfreibetrag"]) / 10000
        return (p["zone2_a"] * y + p["zone2_b"]) * y
    elif zvE <= p["grenze_zone3"]:
        z = (zvE - p["grenze_zone2"]) / 10000
        return (p["zone3_a"] * z + p["zone3_b"]) * z + p["zone3_T1"]
    elif zvE <= p["grenze_zone4"]:
        return p["zone4_rate"] * zvE - p["zone4_offset"]
    else:
        return p["zone5_rate"] * zvE - p["zone5_offset"]


def _vorsorgepauschale(annual_gross: float) -> float:
    """Vereinfachte Vorsorgepauschale für GKV-Arbeitnehmer (West, 2026)."""
    p = TAX_PARAMS_2026
    rv = min(annual_gross, p["bbg_rv"]) * p["rv_an_satz"]
    kv = min(annual_gross, p["bbg_kv"]) * p["kv_an_satz"]
    pv = min(annual_gross, p["bbg_kv"]) * p["pv_an_satz"]
    return rv + kv + pv


def calculate_annual_tax(annual_income: float, tax_class: int) -> Tuple[float, float]:
    """
    Berechnet die Jahres-Lohnsteuer nach § 32a EStG 2026.
    Gibt (Lohnsteuer, Solidaritätszuschlag) zurück.
    
    Berücksichtigt Arbeitnehmer-Pauschbetrag, Sonderausgaben-Pauschbetrag,
    vereinfachte Vorsorgepauschale und Steuerklassen-spezifische Regelungen.
    """
    p = TAX_PARAMS_2026
    ap = p["arbeitnehmer_pauschbetrag"]
    so = p["sonderausgaben_pauschbetrag"]
    vorsorge = _vorsorgepauschale(annual_income)

    if tax_class == 3:
        # Ehegattensplitting: § 32a Abs. 5 EStG
        zvE = max(0.0, annual_income - ap - so - vorsorge)
        tax = 2.0 * _grundtarif_2026(zvE / 2)
    elif tax_class == 2:
        # Alleinerziehend: Entlastungsbetrag § 24b EStG
        entlastung = p["entlastungsbetrag_alleinerziehend"]
        zvE = max(0.0, annual_income - ap - so - vorsorge - entlastung)
        tax = _grundtarif_2026(zvE)
    elif tax_class == 5:
        # SK5: kein GFB, kein AN-Pauschbetrag, aber Vorsorgepauschale
        zvE = max(0.0, annual_income - so - vorsorge)
        tax = _grundtarif_2026(zvE + p["grundfreibetrag"])
    elif tax_class == 6:
        # SK6 (Zweitjob): kein GFB, kein AN-Pauschbetrag, KEINE Vorsorgepauschale
        # (VSP = 0 im BMF-PAP, da SV-Beiträge beim Hauptarbeitgeber abgeführt)
        zvE = max(0.0, annual_income - so)
        tax = _grundtarif_2026(zvE + p["grundfreibetrag"])
    else:
        # SK 1, 4: Standard-Grundtarif
        zvE = max(0.0, annual_income - ap - so - vorsorge)
        tax = _grundtarif_2026(zvE)

    tax = max(0.0, round(tax))

    # Solidaritätszuschlag mit Freigrenze und Milderungszone (§ 3 Abs. 3, § 4 SolZG 1995)
    # Freigrenze: doppelt für SK III (Splitting), einfach für alle anderen SK
    freigrenze = p["solz_freigrenze_splitting"] if tax_class == 3 else p["solz_freigrenze_einzel"]
    if tax <= freigrenze:
        solidarity = 0.0
    else:
        full_solz = p["solidarity_rate"] * tax
        milderung_solz = p["solidarity_milderung"] * (tax - freigrenze)
        solidarity = round(min(full_solz, milderung_solz), 2)

    return tax, solidarity


def calculate_monthly_tax(monthly_income: float, tax_class: int) -> Tuple[float, float]:
    """
    Berechnet die monatliche Lohnsteuer basierend auf Jahreseinkommen.
    """
    annual_income = monthly_income * 12
    annual_tax, annual_solidarity = calculate_annual_tax(annual_income, tax_class)
    
    monthly_tax = annual_tax / 12
    monthly_solidarity = annual_solidarity / 12
    
    return monthly_tax, monthly_solidarity


def calculate_church_tax(lohnsteuer: float) -> float:
    """
    Berechnet die Kirchensteuer als 9% der Lohnsteuer.
    """
    return lohnsteuer * 0.09


def generate_tax_records(
    monthly_income: float,
    tax_class: int,
    kfb_values: List[float]
) -> List[Dict]:
    """
    Generiert für ein bestimmtes monatliches Einkommen und eine Steuerklasse
    Datensätze für alle KFB-Werte.
    
    Mit Kinderfreibetrag wird ein reduziertes zu versteuerndes Einkommen angerechnet.
    """
    records = []
    
    # Berechnung ohne KFB
    lohnsteuer_base, solz_base = calculate_monthly_tax(monthly_income, tax_class)
    
    for kfb in kfb_values:
        # Mit KFB wird ein gewisser Betrag vom Einkommen abgezogen
        # KFB 1 = 100€ pro Monat (2.400€ jährlich / 24 KFB-Halte)
        # Vereinfachung: KFB reduziert das Einkommen direkt
        kfb_monthly_reduction = kfb * 50  # Vereinfachte Annahme: 1 KFB = 50€/Monat
        adjusted_income = max(0, monthly_income - kfb_monthly_reduction)
        
        lohnsteuer, solz = calculate_monthly_tax(adjusted_income, tax_class)
        kist = calculate_church_tax(lohnsteuer)
        
        record = {
            "Einkommen_EUR": monthly_income,
            "Steuerklasse": tax_class,
            "Kinderfreibetrag": kfb,
            "Lohnsteuer": round(lohnsteuer, 2),
            "SolZ": round(solz, 2),
            "Kirchensteuer_9%": round(kist, 2),
        }
        records.append(record)
    
    return records


def generate_2026_tax_table(
    income_min: float = 1000,
    income_max: float = 10000,
    step: float = 5,
    tax_classes: Optional[List[int]] = None,
    kfb_values: Optional[List[float]] = None,
) -> pd.DataFrame:
    """
    Generiert die komplette Steuertabelle für 2026.
    """
    if tax_classes is None:
        tax_classes = [1, 2, 3, 4, 5, 6]
    if kfb_values is None:
        kfb_values = KFB_VALUES
    
    all_records = []
    
    # Generiere alle Einkommensstufen
    income = income_min
    while income <= income_max + 0.01:  # Floating-point tolerance
        for tax_class in tax_classes:
            records = generate_tax_records(income, tax_class, kfb_values)
            all_records.extend(records)
        income += step
    
    df = pd.DataFrame(all_records)
    
    # Spalten sortieren
    return df[["Einkommen_EUR", "Steuerklasse", "Kinderfreibetrag", 
               "Lohnsteuer", "SolZ", "Kirchensteuer_9%"]]


def build_wide_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transformiert die Rohdaten in eine breite Tabelle (wie in der Originalanwendung).
    """
    if df.empty:
        return pd.DataFrame(columns=["Einkommen_EUR", "Steuerklasse", "Lohnsteuer"])
    
    key_cols = ["Einkommen_EUR", "Steuerklasse"]
    
    # Basis: Lohnsteuer (einmalig pro Einkommen + Steuerklasse)
    wide = (
        df[key_cols + ["Lohnsteuer"]]
        .groupby(key_cols, as_index=False)
        .agg(Lohnsteuer=("Lohnsteuer", "first"))
        .sort_values(by=key_cols)
        .reset_index(drop=True)
    )
    
    # KFB-Werte als Spalten hinzufügen
    for kfb in KFB_VALUES:
        kfb_label = str(int(kfb)) if float(kfb).is_integer() else str(kfb).replace(".", ",")
        kfb_df = (
            df[df["Kinderfreibetrag"] == kfb][key_cols + ["SolZ", "Kirchensteuer_9%"]]
            .groupby(key_cols, as_index=False)
            .first()
            .rename(columns={
                "SolZ": f"KFB_{kfb_label}_SolZ",
                "Kirchensteuer_9%": f"KFB_{kfb_label}_KiSt_9%",
            })
        )
        wide = wide.merge(kfb_df, on=key_cols, how="left")
    
    return wide


def write_excel_file(
    output_path: Path,
    wide_df: pd.DataFrame,
    raw_df: pd.DataFrame,
    main_sheet: str = "Tabelle",
    raw_sheet: str = "Tabelle_Rohdaten",
) -> None:
    """
    Schreibt die Excel-Datei mit Hauptblatt und Rohdatenblatt.
    """
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        wide_df.to_excel(writer, sheet_name=main_sheet, index=False)
        raw_df.to_excel(writer, sheet_name=raw_sheet, index=False)
    
    print(f"✓ Excel-Datei geschrieben: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Generiert eine Lohnsteuertabelle für 2026"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="Lohnsteuer_2026_West_monatlich.xlsx",
        help="Pfad zur Ausgabe-Excel-Datei"
    )
    parser.add_argument(
        "--income-min",
        type=float,
        default=1000,
        help="Minimales monatliches Einkommen (EUR)"
    )
    parser.add_argument(
        "--income-max",
        type=float,
        default=10000,
        help="Maximales monatliches Einkommen (EUR)"
    )
    parser.add_argument(
        "--step",
        type=float,
        default=5,
        help="Schrittweite der Einkommenswerte (EUR)"
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("GENERIERUNG LOHNSTEUERTABELLE 2026")
    print("=" * 70)
    print(f"Einkommensbereiche: {args.income_min}€ - {args.income_max}€")
    print(f"Schrittweite: {args.step}€")
    print(f"Steuerklassen: 1-6")
    print(f"Kinderfreibeträge: {KFB_VALUES}")
    print(f"Kirchensteuersatz: 9%")
    print(f"Region: West (monatlich)")
    print()
    
    print("Generiere Rohdaten...")
    raw_df = generate_2026_tax_table(
        income_min=args.income_min,
        income_max=args.income_max,
        step=args.step,
    )
    print(f"✓ {len(raw_df)} Datensätze generiert")
    
    print("Generiere strukturierte Haupttabelle...")
    wide_df = build_wide_dataframe(raw_df)
    print(f"✓ {len(wide_df)} Zeilen in Haupttabelle")
    
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print()
    print("Schreibe Excel-Datei...")
    write_excel_file(output_path, wide_df, raw_df)
    
    print()
    print("=" * 70)
    print("✓ FERTIG")
    print("=" * 70)
    print(f"Ausgabedatei: {output_path.absolute()}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
