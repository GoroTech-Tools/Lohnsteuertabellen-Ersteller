# -*- coding: utf-8 -*-
"""Template für Tarifdaten 2027 (noch nicht freigeschaltet)."""

from __future__ import annotations

# ---------------------------------------------------------------------------
# WICHTIG:
# - Dieses Modul ist eine Vorlage und wird aktuell NICHT von der Anwendung genutzt.
# - Sobald BMF-Zahlen final vorliegen, die Platzhalter ersetzen und das Jahr in
#   src/available_tax_years.py unter SUPPORTED_TAX_YEARS aktiv registrieren.
# ---------------------------------------------------------------------------

YEAR = 2027
IS_ACTIVE = False

# TODO: Nach Veröffentlichung der finalen BMF-Werte für 2027 ausfüllen.
TAX_PARAMS_2027: dict[str, float] = {
    # Beispielhafte Schlüsselstruktur (an 2026 ausgerichtet):
    # "grundfreibetrag": ...,
    # "grenze_zone2": ...,
    # "grenze_zone3": ...,
    # "grenze_zone4": ...,
    # "zone2_a": ...,
    # "zone2_b": ...,
    # "zone3_a": ...,
    # "zone3_b": ...,
    # "zone3_T1": ...,
    # "zone4_rate": ...,
    # "zone4_offset": ...,
    # "zone5_rate": ...,
    # "zone5_offset": ...,
    # "solidarity_rate": ...,
    # "solidarity_milderung": ...,
    # "solz_freigrenze_einzel": ...,
    # "solz_freigrenze_splitting": ...,
    # "arbeitnehmer_pauschbetrag": ...,
    # "sonderausgaben_pauschbetrag": ...,
    # "entlastungsbetrag_alleinerziehend": ...,
    # "rv_an_satz": ...,
    # "kv_an_satz": ...,
    # "pv_an_satz": ...,
    # "bbg_rv": ...,
    # "bbg_kv": ...,
}

# TODO: Bei Aktivierung mit den tatsächlichen KFB-Werten pflegen.
KFB_VALUES_2027: list[float] = []
