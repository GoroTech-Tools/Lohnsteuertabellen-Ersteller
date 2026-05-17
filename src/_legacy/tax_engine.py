# -*- coding: utf-8 -*-
"""Generische Rechenhilfen für Lohnsteuertabellen."""

from __future__ import annotations

from typing import Dict, Iterable


TaxParams = Dict[str, float]



def grundtarif(zvE: float, tax_params: TaxParams) -> float:
    """Berechnet den Grundtarif für die übergebenen Tarifparameter."""
    p = tax_params
    zvE = int(zvE)
    if zvE <= p["grundfreibetrag"]:
        return 0.0
    if zvE <= p["grenze_zone2"]:
        y = (zvE - p["grundfreibetrag"]) / 10000
        return (p["zone2_a"] * y + p["zone2_b"]) * y
    if zvE <= p["grenze_zone3"]:
        z = (zvE - p["grenze_zone2"]) / 10000
        return (p["zone3_a"] * z + p["zone3_b"]) * z + p["zone3_T1"]
    if zvE <= p["grenze_zone4"]:
        return p["zone4_rate"] * zvE - p["zone4_offset"]
    return p["zone5_rate"] * zvE - p["zone5_offset"]



def vorsorgepauschale(annual_gross: float, tax_params: TaxParams) -> float:
    """Berechnet die vereinfachte Vorsorgepauschale für das gewählte Jahr."""
    p = tax_params
    rv = min(annual_gross, p["bbg_rv"]) * p["rv_an_satz"]
    kv = min(annual_gross, p["bbg_kv"]) * p["kv_an_satz"]
    pv = min(annual_gross, p["bbg_kv"]) * p["pv_an_satz"]
    return rv + kv + pv



def calculate_annual_tax_for_year(
    annual_income: float,
    tax_class: int,
    tax_params: TaxParams,
) -> tuple[float, float]:
    """Berechnet Jahres-Lohnsteuer und Solidaritätszuschlag für gegebene Tarifparameter."""
    p = tax_params
    ap = p["arbeitnehmer_pauschbetrag"]
    so = p["sonderausgaben_pauschbetrag"]
    vsp = vorsorgepauschale(annual_income, p)

    if tax_class == 3:
        zvE = max(0.0, annual_income - ap - so - vsp)
        tax = 2.0 * grundtarif(zvE / 2, p)
    elif tax_class == 2:
        zvE = max(0.0, annual_income - ap - so - vsp - p["entlastungsbetrag_alleinerziehend"])
        tax = grundtarif(zvE, p)
    elif tax_class == 5:
        zvE = max(0.0, annual_income - so - vsp)
        tax = grundtarif(zvE + p["grundfreibetrag"], p)
    elif tax_class == 6:
        zvE = max(0.0, annual_income - so)
        tax = grundtarif(zvE + p["grundfreibetrag"], p)
    else:
        zvE = max(0.0, annual_income - ap - so - vsp)
        tax = grundtarif(zvE, p)

    tax = max(0.0, round(tax))

    freigrenze = p["solz_freigrenze_splitting"] if tax_class == 3 else p["solz_freigrenze_einzel"]
    if tax <= freigrenze:
        solidarity = 0.0
    else:
        full_solz = p["solidarity_rate"] * tax
        milderung_solz = p["solidarity_milderung"] * (tax - freigrenze)
        solidarity = round(min(full_solz, milderung_solz), 2)

    return tax, solidarity



def calculate_monthly_tax_for_year(
    monthly_income: float,
    tax_class: int,
    tax_params: TaxParams,
) -> tuple[float, float]:
    """Berechnet monatliche Lohnsteuer und SolZ für gegebene Tarifparameter."""
    annual_tax, annual_solidarity = calculate_annual_tax_for_year(monthly_income * 12, tax_class, tax_params)
    return annual_tax / 12, annual_solidarity / 12



def calculate_church_tax(lohnsteuer: float, rate: float = 0.09) -> float:
    """Berechnet die Kirchensteuer als Prozentsatz der Lohnsteuer."""
    return lohnsteuer * rate



def _calculate_jbmg(
    annual_income: float,
    tax_class: int,
    kfb_annual: int,
    tax_params: TaxParams,
) -> float:
    """
    Berechnet die Jahressteuer nach § 51a EStG (JBMG).

    JBMG ist die Bemessungsgrundlage fuer Solidaritaetszuschlag und Kirchensteuer.
    Gegenueber LSTJAHR wird zusaetzlich das Kinderfreibetrag-Jahresvolumen (kfb_annual)
    vom zu versteuernden Einkommen abgezogen.
    """
    p = tax_params
    ap = p["arbeitnehmer_pauschbetrag"]
    so = p["sonderausgaben_pauschbetrag"]
    vsp = vorsorgepauschale(annual_income, p)

    if tax_class == 3:
        zvE = max(0.0, annual_income - ap - so - vsp - kfb_annual)
        return max(0.0, round(2.0 * grundtarif(zvE / 2, p)))
    elif tax_class == 2:
        zvE = max(0.0, annual_income - ap - so - vsp - p["entlastungsbetrag_alleinerziehend"] - kfb_annual)
        return max(0.0, round(grundtarif(zvE, p)))
    elif tax_class == 5:
        zvE = max(0.0, annual_income - so - vsp - kfb_annual)
        return max(0.0, round(grundtarif(zvE + p["grundfreibetrag"], p)))
    elif tax_class == 6:
        zvE = max(0.0, annual_income - so - kfb_annual)
        return max(0.0, round(grundtarif(zvE + p["grundfreibetrag"], p)))
    else:  # SK 1, 4
        zvE = max(0.0, annual_income - ap - so - vsp - kfb_annual)
        return max(0.0, round(grundtarif(zvE, p)))



def generate_tax_records_for_year(
    monthly_income: float,
    tax_class: int,
    kfb_values: Iterable[float],
    tax_params: TaxParams,
    church_tax_rate: float = 0.09,
) -> list[dict[str, float]]:
    """Erzeugt Rohdatensätze für eine Einkommensstufe und Steuerklasse."""
    records: list[dict[str, float]] = []
    p = tax_params

    for kfb in kfb_values:
        # LSTLZZ: Jahreslohnsteuer OHNE KFB-Abzug (§ 39b Abs. 2 EStG)
        lohnsteuer, _ = calculate_monthly_tax_for_year(monthly_income, tax_class, p)

        # KFB-Jahresbetrag gemaess PAP MZTABFB
        if tax_class in (1, 2, 3):
            kfb_annual = int(kfb * p.get("kfb_faktor_sk123", 9756))
        elif tax_class == 4:
            kfb_annual = int(kfb * p.get("kfb_faktor_sk4", 4878))
        else:  # SK 5, 6
            kfb_annual = 0

        # JBMG: Jahressteuer nach § 51a EStG (mit KFB-Abzug)
        jbmg = _calculate_jbmg(monthly_income * 12, tax_class, kfb_annual, p)

        # SolZ: Bemessungsgrundlage ist JBMG (nicht LSTJAHR)
        freigrenze = p["solz_freigrenze_splitting"] if tax_class == 3 else p["solz_freigrenze_einzel"]
        if jbmg <= freigrenze:
            solz = 0.0
        else:
            full_solz   = p["solidarity_rate"] * jbmg
            milderung   = p["solidarity_milderung"] * (jbmg - freigrenze)
            solz = round(min(full_solz, milderung) / 12, 2)

        # Kirchensteuer: Bemessungsgrundlage ist ebenfalls JBMG
        kist = round(jbmg / 12 * church_tax_rate, 2)

        records.append(
            {
                "Einkommen_EUR": monthly_income,
                "Steuerklasse": tax_class,
                "Kinderfreibetrag": kfb,
                "Lohnsteuer": round(lohnsteuer, 2),
                "SolZ": solz,
                "Kirchensteuer_9%": kist,
            }
        )

    return records
