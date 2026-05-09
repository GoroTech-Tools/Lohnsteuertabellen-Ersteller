# -*- coding: utf-8 -*-
"""Zentrale Konfiguration für das aktuell unterstützte Steuerjahr."""

from __future__ import annotations

TAX_YEAR = 2026
DEFAULT_REGION = "West"
DEFAULT_PERIOD_LABEL = "monatlich"


def get_sheet_names(year: int = TAX_YEAR) -> tuple[str, str]:
    """Liefert die standardisierten Blattnamen für Haupt- und Rohdatenblatt."""
    return f"Lohnsteuer_{year}", f"Lohnsteuer_Rohdaten_{year}"



def get_output_filename(
    year: int = TAX_YEAR,
    region: str = DEFAULT_REGION,
    period_label: str = DEFAULT_PERIOD_LABEL,
) -> str:
    """Liefert den Standard-Dateinamen für den Excel-Export."""
    return f"Lohnsteuer_{year}_{region}_{period_label}.xlsx"



def get_generation_title(year: int = TAX_YEAR) -> str:
    """Liefert den Konsolentitel für die Generierung."""
    return f"GENERIERUNG LOHNSTEUERTABELLE {year}"
