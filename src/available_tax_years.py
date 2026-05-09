# -*- coding: utf-8 -*-
"""Zentrale Registry für unterstützte Steuerjahre."""

from __future__ import annotations

import importlib
from pathlib import Path
from dataclasses import dataclass
from typing import Callable, TypedDict

from generate_2026_tax_table import generate_tax_table
from tax_year_config import TAX_YEAR

GeneratorFn = Callable[..., object]


class ActivationSummary(TypedDict):
    """Rückgabetyp von get_pending_activation_summary."""
    year: int
    all_passed: bool
    passed: int
    failed: int
    checks: list[TemplateChecklistItem]


@dataclass(frozen=True)
class TaxYearRegistration:
    """Beschreibt ein unterstütztes Steuerjahr."""

    year: int
    label: str
    generator: GeneratorFn


@dataclass(frozen=True)
class PendingTaxYearTemplate:
    """Beschreibt ein vorbereitetes, aber noch nicht aktiviertes Steuerjahr."""

    year: int
    label: str
    data_module: str
    note: str


@dataclass(frozen=True)
class TemplateChecklistItem:
    """Ein einzelner Prüfschritt für die Aktivierung eines neuen Steuerjahres."""

    key: str
    description: str
    passed: bool
    details: str


SUPPORTED_TAX_YEARS: dict[int, TaxYearRegistration] = {
    TAX_YEAR: TaxYearRegistration(
        year=TAX_YEAR,
        label=f"Lohnsteuer {TAX_YEAR}",
        generator=generate_tax_table,
    )
}


PENDING_TAX_YEAR_TEMPLATES: dict[int, PendingTaxYearTemplate] = {
    2027: PendingTaxYearTemplate(
        year=2027,
        label="Lohnsteuer 2027 (Template, noch nicht aktiv)",
        data_module="tax_data_2027.py",
        note="Finale BMF-Werte einpflegen und anschließend unter SUPPORTED_TAX_YEARS registrieren.",
    )
}


DEFAULT_TAX_YEAR = max(SUPPORTED_TAX_YEARS)


def get_supported_years() -> list[int]:
    """Liefert alle unterstützten Steuerjahre aufsteigend sortiert."""
    return sorted(SUPPORTED_TAX_YEARS)


def get_default_tax_year() -> int:
    """Liefert das Standard-Steuerjahr für die UI."""
    return DEFAULT_TAX_YEAR


def get_year_registration(year: int) -> TaxYearRegistration | None:
    """Liefert die Registry-Information für ein Jahr oder None."""
    return SUPPORTED_TAX_YEARS.get(year)


def get_available_generators() -> dict[int, GeneratorFn]:
    """Liefert ein Jahr->Generator-Mapping für die Anwendung."""
    return {year: registration.generator for year, registration in SUPPORTED_TAX_YEARS.items()}


def get_pending_year_templates() -> list[PendingTaxYearTemplate]:
    """Liefert vorbereitete, aber noch nicht freigeschaltete Jahres-Templates."""
    return [PENDING_TAX_YEAR_TEMPLATES[year] for year in sorted(PENDING_TAX_YEAR_TEMPLATES)]


def _module_name_from_template(template: PendingTaxYearTemplate) -> str:
    """Leitet den Python-Modulnamen aus dem hinterlegten Dateinamen ab."""
    return Path(template.data_module).stem


def get_pending_activation_checklist(year: int) -> list[TemplateChecklistItem]:
    """Prüft ein vorbereitetes Jahr auf Aktivierungsreife.

    Rückgabe enthält einzelne Checkpunkte mit pass/fail und Details.
    """
    template = PENDING_TAX_YEAR_TEMPLATES.get(year)
    if template is None:
        return [
            TemplateChecklistItem(
                key="template_exists",
                description="Template-Eintrag in PENDING_TAX_YEAR_TEMPLATES vorhanden",
                passed=False,
                details=f"Kein Pending-Template für Jahr {year} gefunden.",
            )
        ]

    checks: list[TemplateChecklistItem] = []
    module_name = _module_name_from_template(template)

    try:
        module = importlib.import_module(module_name)
        checks.append(
            TemplateChecklistItem(
                key="module_importable",
                description="Datenmodul ist importierbar",
                passed=True,
                details=f"Modul '{module_name}' erfolgreich importiert.",
            )
        )
    except Exception as exc:
        checks.append(
            TemplateChecklistItem(
                key="module_importable",
                description="Datenmodul ist importierbar",
                passed=False,
                details=f"Modul '{module_name}' konnte nicht importiert werden: {exc}",
            )
        )
        return checks

    params_name = f"TAX_PARAMS_{year}"
    kfb_name = f"KFB_VALUES_{year}"

    tax_params = getattr(module, params_name, None)
    kfb_values = getattr(module, kfb_name, None)
    is_active = getattr(module, "IS_ACTIVE", None)

    checks.append(
        TemplateChecklistItem(
            key="tax_params_present",
            description=f"{params_name} ist vorhanden und nicht leer",
            passed=isinstance(tax_params, dict) and len(tax_params) > 0,
            details="Tarifparameter fehlen oder sind leer." if not (isinstance(tax_params, dict) and len(tax_params) > 0) else "Tarifparameter sind befüllt.",
        )
    )

    checks.append(
        TemplateChecklistItem(
            key="kfb_values_present",
            description=f"{kfb_name} ist vorhanden und nicht leer",
            passed=isinstance(kfb_values, list) and len(kfb_values) > 0,
            details="KFB-Werte fehlen oder sind leer." if not (isinstance(kfb_values, list) and len(kfb_values) > 0) else "KFB-Werte sind befüllt.",
        )
    )

    checks.append(
        TemplateChecklistItem(
            key="still_inactive",
            description="Template ist weiterhin als inaktiv markiert (IS_ACTIVE=False)",
            passed=is_active is False,
            details="IS_ACTIVE ist nicht explizit False gesetzt." if is_active is not False else "IS_ACTIVE=False ist korrekt gesetzt.",
        )
    )

    checks.append(
        TemplateChecklistItem(
            key="not_registered_as_supported",
            description="Jahr ist noch nicht in SUPPORTED_TAX_YEARS registriert",
            passed=year not in SUPPORTED_TAX_YEARS,
            details="Jahr ist bereits aktiv registriert." if year in SUPPORTED_TAX_YEARS else "Jahr ist korrekt nur als Pending-Template geführt.",
        )
    )

    return checks


def get_pending_activation_summary(year: int) -> ActivationSummary:
    """Liefert eine kompakte Zusammenfassung der Aktivierungschecks."""
    checks = get_pending_activation_checklist(year)
    all_passed = all(check.passed for check in checks)
    return {
        "year": year,
        "all_passed": all_passed,
        "passed": sum(1 for check in checks if check.passed),
        "failed": sum(1 for check in checks if not check.passed),
        "checks": checks,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Entwickler-Tool: Aktivierungsstatus eines Steuerjahres prüfen."
    )
    parser.add_argument(
        "--check",
        metavar="JAHR",
        type=int,
        help="Ausstehende Aktivierungs-Checkliste für das angegebene Jahr anzeigen.",
    )
    args = parser.parse_args()

    if args.check:
        year = args.check
        summary = get_pending_activation_summary(year)
        status = "BEREIT" if summary["all_passed"] else "NOCH NICHT BEREIT"
        print(f"\nAktivierungsstatus für {year}: {status}")
        print(f"  Bestanden: {summary['passed']}  |  Offen: {summary['failed']}\n")
        for check in summary["checks"]:
            symbol = "✓" if check.passed else "✗"
            print(f"  {symbol} [{check.key}]  {check.description}")
            if not check.passed:
                print(f"      → {check.details}")
        print()
    else:
        parser.print_help()
