# -*- coding: utf-8 -*-
"""
Standalone-Generator für Lohnsteuertabelle 2026
Erstellt Excel-Datei direkt ohne externe venv-Abhängigkeiten
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# ===================== 2026 TARIFPARAMETER =====================
# Quelle: § 32a Abs. 1 EStG, Fassung ab Veranlagungszeitraum 2026
TAX_PARAMS_2026 = {
    # Tarifzonen
    "grundfreibetrag":  12348,
    "grenze_zone2":     17799,
    "grenze_zone3":     69878,
    "grenze_zone4":    277825,
    # Zone 2: (914,51 · y + 1.400) · y
    "zone2_a":   914.51,
    "zone2_b":  1400.0,
    # Zone 3: (173,10 · z + 2.397) · z + 1.034,87
    "zone3_a":   173.10,
    "zone3_b":  2397.0,
    "zone3_T1": 1034.87,
    # Zone 4: 0,42 · x − 11.135,63
    "zone4_rate":    0.42,
    "zone4_offset": 11135.63,
    # Zone 5: 0,45 · x − 19.470,38
    "zone5_rate":    0.45,
    "zone5_offset": 19470.38,
    "solidarity_rate":           0.055,   # 5,5 % der Lohnsteuer
    "solidarity_milderung":      0.119,   # Milderungszone § 4 SolZG: max. 11,9 % des Übersteigungsbetrags
    # Freigrenze § 3 Abs. 3 SolZG 1995 (Jahres-Lohnsteuer)
    "solz_freigrenze_einzel":   20350,   # SK I, II, IV, V, VI
    "solz_freigrenze_splitting": 40700,   # SK III (Ehegattensplitting)
    # Pauschbeträge
    "arbeitnehmer_pauschbetrag":        1230,
    "sonderausgaben_pauschbetrag":        36,
    "entlastungsbetrag_alleinerziehend": 4260,
    # SV-Beitragssätze (AN-Anteil, West 2026)
    "rv_an_satz":  0.0930,
    "kv_an_satz":  0.0815,
    "pv_an_satz":  0.0180,
    "bbg_rv":     89400,
    "bbg_kv":     66150,
}

KFB_VALUES = [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4]

def _grundtarif_2026(zvE: float) -> float:
    """§ 32a Abs. 1 EStG 2026"""
    p = TAX_PARAMS_2026
    zvE = int(zvE)
    if zvE <= p["grundfreibetrag"]:
        return 0.0
    elif zvE <= p["grenze_zone2"]:
        y = (zvE - p["grundfreibetrag"]) / 10000
        return (p["zone2_a"] * y + p["zone2_b"]) * y
    elif zvE <= p["grenze_zone3"]:
        z = (zvE - p["grenze_zone2"]) / 10000
        return (p["zone3_a"] * z + p["zone3_b"]) * z + p["zone3_T1"]
    elif zvE <= p["grenze_zone4"]:
        return p["zone4_rate"] * zvE - p["zone4_offset"]
    else:
        return p["zone5_rate"] * zvE - p["zone5_offset"]


def _vorsorgepauschale(annual_gross: float) -> float:
    """Vereinfachte Vorsorgepauschale (GKV-AN, West 2026)."""
    p = TAX_PARAMS_2026
    rv = min(annual_gross, p["bbg_rv"]) * p["rv_an_satz"]
    kv = min(annual_gross, p["bbg_kv"]) * p["kv_an_satz"]
    pv = min(annual_gross, p["bbg_kv"]) * p["pv_an_satz"]
    return rv + kv + pv


def calculate_monthly_tax(monthly_income: float, tax_class: int) -> tuple:
    """Berechnet monatliche Lohnsteuer und SolZ"""
    p = TAX_PARAMS_2026
    ap = p["arbeitnehmer_pauschbetrag"]
    so = p["sonderausgaben_pauschbetrag"]
    annual_gross = monthly_income * 12
    vorsorge = _vorsorgepauschale(annual_gross)

    if tax_class == 3:
        zvE = max(0.0, annual_gross - ap - so - vorsorge)
        annual_tax = 2.0 * _grundtarif_2026(zvE / 2)
    elif tax_class == 2:
        zvE = max(0.0, annual_gross - ap - so - vorsorge - p["entlastungsbetrag_alleinerziehend"])
        annual_tax = _grundtarif_2026(zvE)
    elif tax_class == 5:
        zvE = max(0.0, annual_gross - so - vorsorge)
        annual_tax = _grundtarif_2026(zvE + p["grundfreibetrag"])
    elif tax_class == 6:
        # SK6: keine Vorsorgepauschale (VSP=0 im BMF-PAP)
        zvE = max(0.0, annual_gross - so)
        annual_tax = _grundtarif_2026(zvE + p["grundfreibetrag"])
    else:  # SK 1, 4
        zvE = max(0.0, annual_gross - ap - so - vorsorge)
        annual_tax = _grundtarif_2026(zvE)

    annual_tax = max(0.0, round(annual_tax))
    monthly_tax = round(annual_tax / 12, 2)

    # Solidaritätszuschlag mit Freigrenze und Milderungszone (§ 3 Abs. 3, § 4 SolZG 1995)
    freigrenze = p["solz_freigrenze_splitting"] if tax_class == 3 else p["solz_freigrenze_einzel"]
    if annual_tax <= freigrenze:
        monthly_solidarity = 0.0
    else:
        full_solz = p["solidarity_rate"] * annual_tax
        milderung_solz = p["solidarity_milderung"] * (annual_tax - freigrenze)
        monthly_solidarity = round(min(full_solz, milderung_solz) / 12, 2)

    return monthly_tax, monthly_solidarity


def generate_excel_table():
    """Erstellt die Excel-Datei mit der Lohnsteuertabelle 2026"""
    
    wb = Workbook()
    ws_main = wb.active
    ws_main.title = "Tabelle"
    
    # Header
    ws_main['A1'] = "Einkommen_EUR"
    ws_main['B1'] = "Steuerklasse"
    ws_main['C1'] = "Lohnsteuer"
    
    col_idx = 4
    for kfb in KFB_VALUES:
        kfb_label = str(int(kfb)) if float(kfb).is_integer() else str(kfb)
        ws_main.cell(row=1, column=col_idx).value = f"KFB_{kfb_label}_SolZ"
        ws_main.cell(row=1, column=col_idx + 1).value = f"KFB_{kfb_label}_KiSt_9%"
        col_idx += 2
    
    # Styling
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    for cell in ws_main[1]:
        if cell.value:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = border
    
    # Daten generieren
    row = 2
    income = 1000
    
    while income <= 10000 + 0.01:
        for tax_class in range(1, 7):
            ws_main.cell(row=row, column=1).value = income
            ws_main.cell(row=row, column=2).value = tax_class
            
            # Lohnsteuer (gleich für alle KFB-Werte bei dieser Einkommensstufe)
            lohnsteuer, _ = calculate_monthly_tax(income, tax_class)
            ws_main.cell(row=row, column=3).value = lohnsteuer
            
            # KFB-Werte
            col_idx = 4
            for kfb in KFB_VALUES:
                # Mit KFB wird das Einkommen reduziert
                kfb_reduction = kfb * 50  # 1 KFB ≈ 50€/Monat (vereinfacht)
                adjusted_income = max(0, income - kfb_reduction)
                
                _, solz = calculate_monthly_tax(adjusted_income, tax_class)
                kist = round(lohnsteuer * 0.09, 2)  # 9% Kirchensteuer
                
                ws_main.cell(row=row, column=col_idx).value = solz
                ws_main.cell(row=row, column=col_idx + 1).value = kist
                col_idx += 2
            
            row += 1
        
        income += 5
    
    # Spaltenbreiten
    ws_main.column_dimensions['A'].width = 15
    ws_main.column_dimensions['B'].width = 14
    ws_main.column_dimensions['C'].width = 14
    for col in range(4, col_idx):
        ws_main.column_dimensions[get_column_letter(col)].width = 14
    
    # Rohdatenblatt (vereinfacht)
    ws_raw = wb.create_sheet("Tabelle_Rohdaten")
    ws_raw['A1'] = "Seite"
    ws_raw['B1'] = "Einkommen_EUR"
    ws_raw['C1'] = "Steuerklasse"
    ws_raw['D1'] = "Kinderfreibetrag"
    ws_raw['E1'] = "Lohnsteuer"
    ws_raw['F1'] = "SolZ"
    ws_raw['G1'] = "Kirchensteuer_9%"
    
    row = 2
    page = 1
    income = 1000
    
    while income <= 10000 + 0.01:
        for tax_class in range(1, 7):
            for kfb in KFB_VALUES:
                kfb_reduction = kfb * 50
                adjusted_income = max(0, income - kfb_reduction)
                
                lohnsteuer, solz = calculate_monthly_tax(income, tax_class)
                _, solz_adjusted = calculate_monthly_tax(adjusted_income, tax_class)
                kist = round(lohnsteuer * 0.09, 2)
                
                ws_raw.cell(row=row, column=1).value = page
                ws_raw.cell(row=row, column=2).value = income
                ws_raw.cell(row=row, column=3).value = tax_class
                ws_raw.cell(row=row, column=4).value = kfb
                ws_raw.cell(row=row, column=5).value = lohnsteuer
                ws_raw.cell(row=row, column=6).value = solz_adjusted
                ws_raw.cell(row=row, column=7).value = kist
                row += 1
        
        income += 5
    
    # Spaltenbreiten für Rohdaten
    for col in range(1, 8):
        ws_raw.column_dimensions[get_column_letter(col)].width = 14
    
    return wb


def main():
    print("=" * 70)
    print("GENERIERUNG LOHNSTEUERTABELLE 2026")
    print("=" * 70)
    print("Einkommensbereiche: 1000€ - 10000€")
    print("Schrittweite: 5€")
    print("Steuerklassen: 1-6")
    print("Kinderfreibeträge: 0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4")
    print("Kirchensteuersatz: 9%")
    print("Region: West (monatlich)")
    print()
    
    # Ausgabedatei im aktuellen Verzeichnis oder src-Verzeichnis
    try:
        output_file = Path(__file__).parent / "Lohnsteuer_2026_West_monatlich.xlsx"
    except:
        output_file = Path("d:/OneDrive/Git-Projekte/Lohnsteuertabellen-Konverter/Lohnsteuer_2026_West_monatlich.xlsx")
    
    print("Generiere Excel-Datei...")
    wb = generate_excel_table()
    
    print(f"Schreibe: {output_file}")
    wb.save(output_file)
    
    print()
    print("=" * 70)
    print("✓ FERTIG")
    print("=" * 70)
    print(f"Ausgabedatei: {output_file.absolute()}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
