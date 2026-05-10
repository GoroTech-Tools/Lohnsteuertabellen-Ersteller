# -*- coding: utf-8 -*-
"""
Lohnsteuertabellen-Generator für 2026.

DEPRECATED: Nutze stattdessen generate_tax_tables_universal für alle Jahre (2006-2026).

Dieser Wrapper bleibt für Rückwärtskompatibilität erhalten und delegiert an das neue
universelle System mit PAP-Parser.
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

import pandas as pd

from tax_year_config import (
    TAX_YEAR,
    get_generation_title,
    get_output_filename,
    get_sheet_names,
)
from generate_tax_tables_universal import generate_tax_table_universal, get_kfb_values_for_year


def generate_2026_tax_table(
    income_min: float = 1000,
    income_max: float = 10000,
    step: float = 5,
    tax_classes: Optional[List[int]] = None,
    kfb_values: Optional[List[float]] = None,
) -> pd.DataFrame:
    """
    Generiert die komplette Steuertabelle für 2026.
    
    DEPRECATED: Nutze generate_tax_table_universal stattdessen.
    """
    return generate_tax_table_universal(
        year=2026,
        income_min=income_min,
        income_max=income_max,
        step=step,
        tax_classes=tax_classes,
        kfb_values=kfb_values,
    )


def generate_tax_table(
    income_min: float = 1000,
    income_max: float = 10000,
    step: float = 5,
    tax_classes: Optional[List[int]] = None,
    kfb_values: Optional[List[float]] = None,
) -> pd.DataFrame:
    """Generischer Alias für 2026 (Rückwärtskompatibilität)."""
    return generate_2026_tax_table(
        income_min=income_min,
        income_max=income_max,
        step=step,
        tax_classes=tax_classes,
        kfb_values=kfb_values,
    )


def build_wide_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transformiert Rohdaten in breite Tabelle (Rückwärtskompatibilität).
    """
    if df.empty:
        return pd.DataFrame(columns=["Einkommen_EUR", "Steuerklasse", "Lohnsteuer"])
    
    kfb_values = get_kfb_values_for_year(2026)
    key_cols = ["Einkommen_EUR", "Steuerklasse"]
    
    # Basis: Lohnsteuer
    wide = (
        df[key_cols + ["Lohnsteuer"]]
        .groupby(key_cols, as_index=False)
        .agg(Lohnsteuer=("Lohnsteuer", "first"))
        .sort_values(by=key_cols)
        .reset_index(drop=True)
    )
    
    # KFB-Spalten hinzufügen
    for kfb in kfb_values:
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
    year: int = 2026,
    main_sheet: Optional[str] = None,
    raw_sheet: Optional[str] = None,
) -> None:
    """Schreibt Excel-Datei mit Haupt- und Rohdatenblatt."""
    default_main_sheet, default_raw_sheet = get_sheet_names(year)
    main_sheet = main_sheet or default_main_sheet
    raw_sheet = raw_sheet or default_raw_sheet

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        wide_df.to_excel(writer, sheet_name=main_sheet, index=False)
        raw_df.to_excel(writer, sheet_name=raw_sheet, index=False)
    
    print(f"✓ Excel-Datei geschrieben: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description=f"Generiert eine Lohnsteuertabelle für 2026 (via PAP-Parser)"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=get_output_filename(2026),
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
        help="Schrittweite (EUR)"
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print(get_generation_title(2026))
    print("=" * 70)
    print(f"Einkommensbereiche: {args.income_min}€ - {args.income_max}€")
    print(f"Schrittweite: {args.step}€")
    print(f"Steuerklassen: 1-6")
    print(f"KFB-Werte: {get_kfb_values_for_year(2026)}")
    print(f"Datenquelle: PAP-Parser (XML-basiert, Multi-Jahr Support)")
    print()
    
    print("Generiere Tabelle...")
    raw_df = generate_2026_tax_table(
        income_min=args.income_min,
        income_max=args.income_max,
        step=args.step,
    )
    print(f"✓ {len(raw_df)} Rohdatensätze")
    
    print("Strukturiere für Excel...")
    wide_df = build_wide_dataframe(raw_df)
    print(f"✓ {len(wide_df)} Haupttabelle-Zeilen")
    
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print()
    write_excel_file(output_path, wide_df, raw_df, year=2026)
    
    print()
    print("=" * 70)
    print("✓ FERTIG")
    print("=" * 70)
    print(f"Ausgabedatei: {output_path.absolute()}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
