# -*- coding: utf-8 -*-
"""
Konfiguration für A/B-Tests der PAP-Integration.

Erlaubt es, zwischen alter Implementierung (tax_engine/tax_data_2026)
und neuer PAP-Parser-Implementierung (lohnsteuer_integration) zu wechseln.
"""

import os
from pathlib import Path

# Feature-Flag: True = verwende PAP-Parser, False = verwende bisherigen tax_engine
# Standard: PAP-Parser aktiviert (zentralisierte Quelle, wartbarer)
USE_PAP_PARSER = os.environ.get("USE_PAP_PARSER", "1").lower() in ("1", "true", "yes")

# Logging-Modus für Debugging
PAP_DEBUG = os.environ.get("PAP_DEBUG", "0").lower() in ("1", "true", "yes")

# Verzeichnis für A/B-Vergleichstabellen (optional)
COMPARISON_OUTPUT_DIR = Path(__file__).parent.parent / "comparison_results"


def enable_pap_parser(enable: bool = True) -> None:
    """Schaltet PAP-Parser zur Laufzeit um (für Tests/Vergleiche)."""
    global USE_PAP_PARSER
    USE_PAP_PARSER = enable
    if PAP_DEBUG:
        print(f"[PAP_DEBUG] PAP_PARSER umgeschaltet: {USE_PAP_PARSER}")


def is_pap_parser_enabled() -> bool:
    """Prüft, ob PAP-Parser aktuell aktiv ist."""
    return USE_PAP_PARSER
