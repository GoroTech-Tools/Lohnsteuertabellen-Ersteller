# -*- coding: utf-8 -*-
"""Tarifdaten und Konstanten für das Steuerjahr 2026."""

from __future__ import annotations

TAX_PARAMS_2026 = {
    # Tarifzonen § 32a EStG 2026
    "grundfreibetrag": 12348,
    "grenze_zone2": 17799,
    "grenze_zone3": 69878,
    "grenze_zone4": 277825,
    # Zone 2: (914,51 · y + 1.400) · y
    "zone2_a": 914.51,
    "zone2_b": 1400.0,
    # Zone 3: (173,10 · z + 2.397) · z + 1.034,87
    "zone3_a": 173.10,
    "zone3_b": 2397.0,
    "zone3_T1": 1034.87,
    # Zone 4: 0,42 · x − 11.135,63
    "zone4_rate": 0.42,
    "zone4_offset": 11135.63,
    # Zone 5: 0,45 · x − 19.470,38
    "zone5_rate": 0.45,
    "zone5_offset": 19470.38,
    # Solidaritätszuschlag (§ 4 SolZG 1995)
    "solidarity_rate": 0.055,
    "solidarity_milderung": 0.119,
    # Freigrenze § 3 Abs. 3 SolZG 1995 (Jahres-Lohnsteuer)
    "solz_freigrenze_einzel": 20350,
    "solz_freigrenze_splitting": 40700,
    # Pauschbeträge für Arbeitnehmer
    "arbeitnehmer_pauschbetrag": 1230,
    "sonderausgaben_pauschbetrag": 36,
    "entlastungsbetrag_alleinerziehend": 4260,
    # Sozialversicherungs-Beitragssätze (Arbeitnehmeranteil, West 2026)
    "rv_an_satz": 0.0930,
    "kv_an_satz": 0.0815,
    "pv_an_satz": 0.0180,
    "bbg_rv": 89400,
    "bbg_kv": 66150,
}

KFB_VALUES_2026 = [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4]
