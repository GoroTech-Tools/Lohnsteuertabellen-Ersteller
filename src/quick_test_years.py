# -*- coding: utf-8 -*-
"""
Schneller Multi-Jahr Test: PAP-Parser für 2024, 2025, 2026.
Reduzierte Datenmenge für schnelle Validierung.
"""

import sys
from pathlib import Path
from lohnsteuer_integration import PAPParser

def quick_test_year(year: int) -> bool:
    """Schneller Test für ein Jahr."""
    try:
        parser = PAPParser()
        # Teste nur 3 verschiedene Einkommen
        for monthly_income in [1500, 5000, 10000]:
            for tax_class in [1, 4]:
                r = parser.berechne_lohnsteuer(
                    bruttolohn=monthly_income,
                    steuerkl=tax_class,
                    jahr=year,
                    lzz=2,
                )
                # Sanity checks
                if r["lohnsteuer"] < 0 or r["soli"] < 0:
                    return False
                if r["soli"] > r["lohnsteuer"]:  # SolZ sollte nicht größer als LS sein
                    return False
        return True
    except Exception as e:
        print(f"  FEHLER: {e}")
        return False

def main():
    print("="*70)
    print("SCHNELLER MULTI-JAHR TEST: PAP-Parser")
    print("="*70 + "\n")
    
    years = [2024, 2025, 2026]
    results = {}
    
    for year in years:
        print(f"[{year}] Teste...", end=" ")
        sys.stdout.flush()
        ok = quick_test_year(year)
        results[year] = ok
        print("✓ OK" if ok else "✗ FEHLER")
    
    print("\n" + "="*70)
    print("ERGEBNIS")
    print("="*70)
    
    for year, ok in results.items():
        status = "✓ ERFOLGREICH" if ok else "✗ FEHLER"
        print(f"{year}: {status}")
    
    success = all(results.values())
    print("\n" + ("✓ Alle Jahre OK" if success else "✗ Einige Jahre fehlgeschlagen"))
    print("="*70 + "\n")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
