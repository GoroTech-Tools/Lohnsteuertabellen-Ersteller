# -*- coding: utf-8 -*-
"""
Generischer Lohnsteuertabellen-Generator für alle Jahre (2006-2026+).
Nutzt PAP-Parser als Standard-Quelle.

Unterstützt:
  - Beliebiges Jahr (solange PAP XML vorhanden)
  - Flexible Steuerklassen und Kinderfreibeträge
  - Fallback zu tax_engine (für kompatibilität mit älteren Jahren ohne tax_data)

Nutzung:
    from generate_tax_tables_universal import generate_tax_table_universal
    df = generate_tax_table_universal(year=2025, income_min=1000, income_max=10000)
"""

from functools import lru_cache
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
import pandas as pd
import sys

from pap_integration_config import is_pap_parser_enabled
from tax_year_config import get_sheet_names, get_output_filename, get_generation_title

# Optionaler PAP-Parser
try:
    from lohnsteuer_integration import PAPParser
    PAP_PARSER_AVAILABLE = True
except ImportError:
    PAP_PARSER_AVAILABLE = False


try:
    from _legacy.tax_data_2026 import TAX_PARAMS_2026
    from _legacy.tax_engine import calculate_monthly_tax_for_year, generate_tax_records_for_year
    TAX_ENGINE_2026_AVAILABLE = True
except ImportError:
    TAX_ENGINE_2026_AVAILABLE = False


@lru_cache(maxsize=1)
def get_shared_pap_parser() -> Any:
    """Erzeugt genau eine PAPParser-Instanz für wiederholte Tabellenläufe."""
    if not PAP_PARSER_AVAILABLE:
        raise RuntimeError(
            "PAP-Parser nicht verfügbar. "
            "Stelle sicher, dass lohnsteuer_integration.py importiert werden kann."
        )

    return PAPParser()


def calculate_annual_tax_universal(
    annual_income: float,
    tax_class: int,
    year: int,
    parser: Optional[Any] = None,
) -> Tuple[float, float]:
    """
    Berechnet Jahres-Lohnsteuer + SolZ für beliebiges Jahr (2006-2026+).
    
    Nutzt PAP-Parser als Standard-Quelle.
    
    Rückgabe: (lohnsteuer_jahr, soli_jahr)
    """
    if year == 2026 and TAX_ENGINE_2026_AVAILABLE:
        monthly_tax, monthly_solidarity = calculate_monthly_tax_for_year(
            annual_income / 12,
            tax_class,
            TAX_PARAMS_2026,
        )
        return monthly_tax * 12, monthly_solidarity * 12

    if not PAP_PARSER_AVAILABLE:
        raise RuntimeError(
            "PAP-Parser nicht verfügbar. "
            "Stelle sicher, dass lohnsteuer_integration.py importiert werden kann."
        )
    
    try:
        if parser is None:
            parser = get_shared_pap_parser()

        # PAPParser wird ohne Jahr initialisiert, Jahr wird in berechne_lohnsteuer übergeben
        result = parser.berechne_lohnsteuer(
            bruttolohn=annual_income / 12,  # Monatlich (lzz=2)
            steuerkl=tax_class,
            jahr=year,
            lzz=2,  # 2 = Monat
        )
        # Hochrechnung auf Jahr
        ls_jahr = result["lohnsteuer"] * 12
        soli_jahr = result["soli"] * 12
        return (ls_jahr, soli_jahr)
    except Exception as e:
        raise ValueError(f"PAP-Parser Fehler für Jahr {year}: {e}")


def get_kfb_values_for_year(year: int) -> List[float]:
    """
    Liefert die Kinderfreibetrag-Werte für ein Jahr.
    
    Aktuell einheitlich für alle Jahre.
    """
    # Standard KFB-Werte (einheitlich über alle Jahre)
    return [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4]


def generate_tax_records_universal(
    monthly_income: float,
    tax_class: int,
    kfb_values: List[float],
    year: int,
    parser: Optional[Any] = None,
) -> List[Dict]:
    """
    Generiert Datensätze für ein Einkommen, alle KFB-Werte.
    
    Für PAP-Parser: wird direkt berechnet.
    Für tax_engine (2026): delegiert an generate_tax_records_for_year.
    """
    if year == 2026 and TAX_ENGINE_2026_AVAILABLE:
        return generate_tax_records_for_year(
            monthly_income,
            tax_class,
            kfb_values,
            TAX_PARAMS_2026,
        )

    if is_pap_parser_enabled() and PAP_PARSER_AVAILABLE:
        if parser is None:
            parser = get_shared_pap_parser()

        # PAP-Parser: Berechne für jedes KFB einzeln mit korrektem ZKF-Parameter
        records = []
        for kfb in kfb_values:
            result = parser.berechne_lohnsteuer(
                bruttolohn=monthly_income,
                jahr=year,
                steuerkl=tax_class,
                lzz=2,  # Monat
                zkf=kfb,
            )
            records.append({
                "Einkommen_EUR": monthly_income,
                "Steuerklasse": tax_class,
                "Kinderfreibetrag": kfb,
                "Lohnsteuer": result["lohnsteuer"],
                "SolZ": result["soli"],
                "Kirchensteuer_9%": result["kirchensteuer_basis"] * 0.09,
            })
        return records
    
    raise RuntimeError(f"Keine Datensatz-Generierung für Jahr {year} möglich.")


def generate_tax_table_universal(
    year: int,
    income_min: float = 1000,
    income_max: float = 10000,
    step: float = 5,
    tax_classes: Optional[List[int]] = None,
    kfb_values: Optional[List[float]] = None,
) -> pd.DataFrame:
    """
    Generiert Lohnsteuertabelle für beliebiges Jahr mit PAP-Parser.
    
    Args:
        year: Steuerjahr (2006-2026)
        income_min: Min. Einkommen (EUR)
        income_max: Max. Einkommen (EUR)
        step: Schrittweite (EUR)
        tax_classes: Steuerklassen (Default: 1-6)
        kfb_values: Kinderfreibeträge (Default: Standard)
    
    Rückgabe: DataFrame mit Spalten [Einkommen_EUR, Steuerklasse, Kinderfreibetrag, ...]
    """
    if tax_classes is None:
        tax_classes = [1, 2, 3, 4, 5, 6]
    if kfb_values is None:
        kfb_values = get_kfb_values_for_year(year)
    
    all_records = []
    parser = get_shared_pap_parser() if (is_pap_parser_enabled() and PAP_PARSER_AVAILABLE) else None
    income = income_min
    while income <= income_max + 0.01:  # Floating-point tolerance
        for tax_class in tax_classes:
            records = generate_tax_records_universal(
                income,
                tax_class,
                kfb_values,
                year,
                parser=parser,
            )
            all_records.extend(records)
        income += step
    
    df = pd.DataFrame(all_records)
    return df[["Einkommen_EUR", "Steuerklasse", "Kinderfreibetrag",
               "Lohnsteuer", "SolZ", "Kirchensteuer_9%"]]
