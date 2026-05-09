# -*- coding: utf-8 -*-
"""
Generiert eine Lohnsteuertabelle für 2026 basierend auf den gültigen Tarifparametern.
Berechnet Lohnsteuer, Solidaritätszuschlag und Kirchensteuer für alle Steuerklassen.

Nutzung:
    python generate_2026_tax_table.py -o "Lohnsteuer_2026_West_monatlich.xlsx"

Parameter:
    - Einkommensbereiche: 1000 - 10000€
    - Steuerklassen: 1-6
    - KFB-Werte: 0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4
    - Kirchensteuersatz: 9%
    - Region: West (monatliche Tabelle)
    - Schrittweite: 5€
"""

import argparse
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import sys

from tax_data_2026 import KFB_VALUES_2026, TAX_PARAMS_2026
from tax_engine import (
    calculate_annual_tax_for_year,
    calculate_church_tax as calculate_church_tax_generic,
    calculate_monthly_tax_for_year,
    generate_tax_records_for_year,
    grundtarif,
    vorsorgepauschale,
)
from tax_year_config import (
    TAX_YEAR,
    get_generation_title,
    get_output_filename,
    get_sheet_names,
)

KFB_VALUES = KFB_VALUES_2026

# ===================== BERECHNUNGSFUNKTIONEN =====================

def _grundtarif_2026(zvE: float) -> float:
    """§ 32a Abs. 1 EStG 2026 – Grundtarif (Grundfreibetrag bereits enthalten)."""
    return grundtarif(zvE, TAX_PARAMS_2026)


def _vorsorgepauschale(annual_gross: float) -> float:
    """Vereinfachte Vorsorgepauschale für GKV-Arbeitnehmer (West, 2026)."""
    return vorsorgepauschale(annual_gross, TAX_PARAMS_2026)


def calculate_annual_tax(annual_income: float, tax_class: int) -> Tuple[float, float]:
    """
    Berechnet die Jahres-Lohnsteuer nach § 32a EStG 2026.
    Gibt (Lohnsteuer, Solidaritätszuschlag) zurück.
    
    Berücksichtigt Arbeitnehmer-Pauschbetrag, Sonderausgaben-Pauschbetrag,
    vereinfachte Vorsorgepauschale und Steuerklassen-spezifische Regelungen.
    """
    return calculate_annual_tax_for_year(annual_income, tax_class, TAX_PARAMS_2026)


def calculate_monthly_tax(monthly_income: float, tax_class: int) -> Tuple[float, float]:
    """
    Berechnet die monatliche Lohnsteuer basierend auf Jahreseinkommen.
    """
    return calculate_monthly_tax_for_year(monthly_income, tax_class, TAX_PARAMS_2026)


def calculate_church_tax(lohnsteuer: float) -> float:
    """
    Berechnet die Kirchensteuer als 9% der Lohnsteuer.
    """
    return calculate_church_tax_generic(lohnsteuer)


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
    return generate_tax_records_for_year(monthly_income, tax_class, kfb_values, TAX_PARAMS_2026)


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


def generate_tax_table(
    income_min: float = 1000,
    income_max: float = 10000,
    step: float = 5,
    tax_classes: Optional[List[int]] = None,
    kfb_values: Optional[List[float]] = None,
) -> pd.DataFrame:
    """Generischer Alias für das aktuell unterstützte Steuerjahr."""
    return generate_2026_tax_table(
        income_min=income_min,
        income_max=income_max,
        step=step,
        tax_classes=tax_classes,
        kfb_values=kfb_values,
    )


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
    year: int = TAX_YEAR,
    main_sheet: Optional[str] = None,
    raw_sheet: Optional[str] = None,
) -> None:
    """
    Schreibt die Excel-Datei mit Hauptblatt und Rohdatenblatt.
    """
    default_main_sheet, default_raw_sheet = get_sheet_names(year)
    main_sheet = main_sheet or default_main_sheet
    raw_sheet = raw_sheet or default_raw_sheet

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        wide_df.to_excel(writer, sheet_name=main_sheet, index=False)
        raw_df.to_excel(writer, sheet_name=raw_sheet, index=False)
    
    print(f"✓ Excel-Datei geschrieben: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description=f"Generiert eine Lohnsteuertabelle für {TAX_YEAR}"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=get_output_filename(TAX_YEAR),
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
    print(get_generation_title(TAX_YEAR))
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
    write_excel_file(output_path, wide_df, raw_df, year=TAX_YEAR)
    
    print()
    print("=" * 70)
    print("✓ FERTIG")
    print("=" * 70)
    print(f"Ausgabedatei: {output_path.absolute()}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
