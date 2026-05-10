# -*- coding: utf-8 -*-
"""
A/B-Test: Vergleicht Ausgabe des tax_engine mit dem PAP-Parser.

Generiert zwei Tabellen:
  1. Mit tax_engine (alt)
  2. Mit PAP-Parser (neu)

Und vergleicht sie zellweise auf Unterschiede.

Nutzung:
    python compare_implementations.py --output-dir comparison_results
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

import pandas as pd

# Lokale Imports
from generate_2026_tax_table import generate_2026_tax_table, build_wide_dataframe, write_excel_file
from pap_integration_config import enable_pap_parser, is_pap_parser_enabled
from tax_year_config import TAX_YEAR


def generate_comparison_tables(output_dir: Path) -> dict:
    """
    Generiert Tabellen mit beiden Implementierungen und speichert sie.
    
    Rückgabe: dict mit Keys 'old', 'new', 'old_path', 'new_path'
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print("\n" + "="*70)
    print("A/B-TEST: tax_engine vs PAP-Parser")
    print("="*70)
    
    # ===== Generation 1: tax_engine (ALT) =====
    print("\n[1/2] Generiere mit tax_engine (bisherige Implementierung)...")
    enable_pap_parser(False)
    assert not is_pap_parser_enabled(), "PAP-Parser sollte deaktiviert sein"
    
    raw_old = generate_2026_tax_table(
        income_min=1000,
        income_max=10000,
        step=5,
    )
    wide_old = build_wide_dataframe(raw_old)
    old_path = output_dir / f"Lohnsteuer_2026_tax_engine_{timestamp}.xlsx"
    write_excel_file(old_path, wide_old, raw_old, year=TAX_YEAR)
    print(f"✓ tax_engine-Tabelle gespeichert: {old_path.name}")
    print(f"  Größe: {len(wide_old)} Zeilen x {len(wide_old.columns)} Spalten")
    
    # ===== Generation 2: PAP-Parser (NEU) =====
    print("\n[2/2] Generiere mit PAP-Parser (neue Implementierung)...")
    enable_pap_parser(True)
    assert is_pap_parser_enabled(), "PAP-Parser sollte aktiviert sein"
    
    try:
        raw_new = generate_2026_tax_table(
            income_min=1000,
            income_max=10000,
            step=5,
        )
        wide_new = build_wide_dataframe(raw_new)
        new_path = output_dir / f"Lohnsteuer_2026_pap_parser_{timestamp}.xlsx"
        write_excel_file(new_path, wide_new, raw_new, year=TAX_YEAR)
        print(f"✓ PAP-Parser-Tabelle gespeichert: {new_path.name}")
        print(f"  Größe: {len(wide_new)} Zeilen x {len(wide_new.columns)} Spalten")
    except Exception as e:
        print(f"✗ Fehler bei PAP-Parser-Generierung: {e}")
        enable_pap_parser(False)  # Fallback
        print("  Fallback auf tax_engine...")
        raw_new = generate_2026_tax_table(
            income_min=1000,
            income_max=10000,
            step=5,
        )
        wide_new = build_wide_dataframe(raw_new)
        new_path = output_dir / f"Lohnsteuer_2026_pap_parser_FALLBACK_{timestamp}.xlsx"
        write_excel_file(new_path, wide_new, raw_new, year=TAX_YEAR)
    
    return {
        "old": (raw_old, wide_old),
        "new": (raw_new, wide_new),
        "old_path": old_path,
        "new_path": new_path,
    }


def compare_tables(tables: dict) -> None:
    """Vergleicht die Tabellen zellweise und zeigt Unterschiede."""
    raw_old, wide_old = tables["old"]
    raw_new, wide_new = tables["new"]
    
    print("\n" + "="*70)
    print("ZELLVERGLEICH")
    print("="*70)
    
    # Vergleich: Breite Tabelle
    print("\n[BREITE TABELLE]")
    same_shape = (wide_old.shape == wide_new.shape)
    print(f"Gleiche Größe: {same_shape}")
    if same_shape:
        print(f"  Shape: {wide_old.shape}")
    else:
        print(f"  tax_engine:   {wide_old.shape}")
        print(f"  PAP-Parser:   {wide_new.shape}")
    
    same_cols = list(wide_old.columns) == list(wide_new.columns)
    print(f"Gleiche Spalten: {same_cols}")
    if not same_cols:
        print(f"  tax_engine:   {list(wide_old.columns)}")
        print(f"  PAP-Parser:   {list(wide_new.columns)}")
    
    # Zellweise Unterschiede
    if same_shape and same_cols:
        differences = []
        for idx, row in wide_old.iterrows():
            for col in wide_old.columns:
                old_val = row[col]
                new_val = wide_new.loc[idx, col] if idx < len(wide_new) else None
                # Numerischer Vergleich (Toleranz: 0.01€)
                if old_val != new_val:
                    if isinstance(old_val, (int, float)) and isinstance(new_val, (int, float)):
                        if abs(old_val - new_val) > 0.01:
                            differences.append((idx, col, old_val, new_val))
                    else:
                        differences.append((idx, col, old_val, new_val))
        
        if differences:
            print(f"\n✗ {len(differences)} UNTERSCHIEDE GEFUNDEN:")
            for idx, col, old_val, new_val in differences[:20]:  # Erste 20
                print(f"  Row {idx}, Spalte '{col}': {old_val} → {new_val}")
            if len(differences) > 20:
                print(f"  ... und {len(differences) - 20} weitere")
        else:
            print("\n✓ KEINE UNTERSCHIEDE in breiter Tabelle")
    
    # Vergleich: Rohdaten
    print("\n[ROHDATEN-TABELLE]")
    same_shape_raw = (raw_old.shape == raw_new.shape)
    print(f"Gleiche Größe: {same_shape_raw}")
    if same_shape_raw:
        print(f"  Shape: {raw_old.shape}")
    else:
        print(f"  tax_engine:   {raw_old.shape}")
        print(f"  PAP-Parser:   {raw_new.shape}")
    
    if same_shape_raw:
        raw_diffs = 0
        for idx, row in raw_old.iterrows():
            for col in raw_old.columns:
                old_val = row[col]
                new_val = raw_new.loc[idx, col] if idx < len(raw_new) else None
                if old_val != new_val:
                    if isinstance(old_val, (int, float)) and isinstance(new_val, (int, float)):
                        if abs(old_val - new_val) > 0.01:
                            raw_diffs += 1
                    else:
                        raw_diffs += 1
        
        if raw_diffs > 0:
            print(f"\n✗ {raw_diffs} UNTERSCHIEDE in Rohdaten")
        else:
            print("\n✓ KEINE UNTERSCHIEDE in Rohdaten")


def main():
    parser = argparse.ArgumentParser(
        description="Vergleicht tax_engine mit PAP-Parser Implementierung"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).parent.parent / "comparison_results",
        help="Ausgabeverzeichnis für Vergleichstabellen",
    )
    
    args = parser.parse_args()
    
    try:
        tables = generate_comparison_tables(args.output_dir)
        compare_tables(tables)
        
        print("\n" + "="*70)
        print(f"Dateien gespeichert in: {args.output_dir.resolve()}")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n✗ Fehler: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
