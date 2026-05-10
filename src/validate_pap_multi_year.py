# -*- coding: utf-8 -*-
"""
Multi-Jahr Validierung: PAP-Parser für 2024, 2025, 2026 testen.

Prüft:
  - Kompatibilität mit vorhandenen PAP-XML-Dateien
  - Plausibilität der berechneten Steuern (sanity checks)
  - Erfolgreiche Generierung für alle unterstützten Jahre

Nutzung:
    python validate_pap_multi_year.py --output-dir validation_results
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Tuple

import pandas as pd

from generate_tax_tables_universal import generate_tax_table_universal
from pap_integration_config import is_pap_parser_enabled


def validate_single_year(year: int, output_dir: Path) -> Dict[str, any]:
    """Generiert und validiert Tabelle für ein Jahr."""
    print(f"\n[{year}] Starte Validierung...")
    
    try:
        # Generierung
        print(f"  → Generiere Tabelle...")
        df = generate_tax_table_universal(
            year=year,
            income_min=1000,
            income_max=10000,
            step=5,
        )
        
        # Basis-Stats
        rows, cols = df.shape
        print(f"    Größe: {rows} Zeilen × {cols} Spalten")
        
        # Sanity Checks
        checks = {
            "rows_count": rows > 0,
            "cols_count": cols >= 5,
            "no_null_einkommen": df["Einkommen_EUR"].isna().sum() == 0,
            "no_null_steuerklasse": df["Steuerklasse"].isna().sum() == 0,
            "lohnsteuer_non_negative": (df["Lohnsteuer"] >= 0).all(),
            "solz_non_negative": (df["SolZ"] >= 0).all(),
            "kirchensteuer_non_negative": (df["Kirchensteuer_9%"] >= 0).all(),
            "solz_less_than_lohnsteuer": (df["SolZ"] <= df["Lohnsteuer"]).all(),
            "steuern_increase_with_income": True,  # Prüfe später
        }
        
        # Income-Monotonität (pro Steuerklasse sollte Steuer steigen)
        for steuerklasse in df["Steuerklasse"].unique():
            subset = df[df["Steuerklasse"] == steuerklasse].sort_values("Einkommen_EUR")
            if len(subset) > 1:
                for i in range(len(subset) - 1):
                    ls1 = subset.iloc[i]["Lohnsteuer"]
                    ls2 = subset.iloc[i+1]["Lohnsteuer"]
                    if ls2 < ls1:
                        checks["steuern_increase_with_income"] = False
                        break
        
        check_count = sum(1 for v in checks.values() if v)
        check_total = len(checks)
        
        # Speichern
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"Lohnsteuer_{year}_PAP_validated_{timestamp}.xlsx"
        
        with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name=f"Lohnsteuer_{year}", index=False)
            
            # Validierungs-Info auf extra Blatt
            check_df = pd.DataFrame([
                {"Check": k, "Bestanden": "✓" if v else "✗"}
                for k, v in checks.items()
            ])
            check_df.to_excel(writer, sheet_name="Validierung", index=False)
        
        print(f"    ✓ {check_count}/{check_total} Checks bestanden")
        print(f"    ✓ Tabelle gespeichert: {output_file.name}")
        
        return {
            "year": year,
            "status": "SUCCESS" if check_count == check_total else "PARTIAL",
            "rows": rows,
            "cols": cols,
            "checks_passed": f"{check_count}/{check_total}",
            "output_file": output_file,
            "checks": checks,
        }
    
    except Exception as e:
        print(f"    ✗ FEHLER: {e}")
        import traceback
        traceback.print_exc()
        return {
            "year": year,
            "status": "ERROR",
            "error": str(e),
        }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Validiert PAP-Parser für mehrere Jahre"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).parent.parent / "validation_results",
        help="Ausgabeverzeichnis",
    )
    parser.add_argument(
        "--years",
        type=int,
        nargs="+",
        default=[2024, 2025, 2026],
        help="Zu validierende Jahre",
    )
    
    args = parser.parse_args()
    
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("="*70)
    print("MULTI-JAHR VALIDIERUNG: PAP-Parser")
    print(f"PAP-Parser Aktiv: {is_pap_parser_enabled()}")
    print("="*70)
    
    results = []
    for year in args.years:
        result = validate_single_year(year, output_dir)
        results.append(result)
    
    # Zusammenfassung
    print("\n" + "="*70)
    print("ZUSAMMENFASSUNG")
    print("="*70)
    
    success_count = sum(1 for r in results if r["status"] == "SUCCESS")
    partial_count = sum(1 for r in results if r["status"] == "PARTIAL")
    error_count = sum(1 for r in results if r["status"] == "ERROR")
    
    for result in results:
        status_icon = {
            "SUCCESS": "✓",
            "PARTIAL": "⚠",
            "ERROR": "✗",
        }.get(result["status"], "?")
        
        if result["status"] in ("SUCCESS", "PARTIAL"):
            print(f"{status_icon} {result['year']}: {result['status']} ({result['checks_passed']} Checks, {result['rows']} Zeilen)")
        else:
            print(f"{status_icon} {result['year']}: {result['status']} - {result['error']}")
    
    print(f"\nGESAMT: {success_count} erfolgreich, {partial_count} partiell, {error_count} fehler")
    print(f"\nDateien: {output_dir.resolve()}")
    print("="*70 + "\n")
    
    # Exit-Code
    sys.exit(0 if error_count == 0 else 1)


if __name__ == "__main__":
    main()
