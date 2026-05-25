# -*- coding: utf-8 -*-
"""
Schlichte GUI zum Erstellen von Lohnsteuertabellen.

Funktionen:
- Eingabe der Jahreszahl
- Auswahl des Speicherorts der Ausgabedatei
- Hinweis + automatisches Schließen bei fehlenden BMF-Tarifdaten
- Setzt app_icon.ico als Anwendungsicon/Titelleistenicon
"""

from __future__ import annotations

import sys
import subprocess
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from available_tax_years import (
    get_available_generators,
    get_default_tax_year,
    get_supported_years,
)
from generate_2026_tax_table import (
    build_wide_dataframe,
    write_excel_file,
)
from tax_year_config import (
    get_output_filename,
)

try:
    from build_version import APP_VERSION
except ImportError:
    APP_VERSION = "dev"

try:
    from embedded_docs import get_temp_doc_path
    EMBEDDED_DOCS_AVAILABLE = True
except ImportError:
    EMBEDDED_DOCS_AVAILABLE = False


ALLOWED_STEPS = (3, 5, 10, 50)
SUPPORTED_YEARS = tuple(get_supported_years())
DEFAULT_YEAR = str(get_default_tax_year())
DEFAULT_STEP = "5"
DEFAULT_INCOME_MIN = "1000"
DEFAULT_INCOME_MAX = "10000"
DEFAULT_OUTPUT = "."
AVAILABLE_GENERATORS = get_available_generators()


class TaxTableGui(tk.Tk):
    def __init__(self) -> None:
        super().__init__()

        self.title(f"Lohnsteuertabellen-Ersteller v{APP_VERSION}")
        self.resizable(False, False)

        self.base_dir = Path(__file__).resolve().parent
        self._set_app_icon()

        self.year_var = tk.StringVar(value=DEFAULT_YEAR)
        self.step_var = tk.StringVar(value=DEFAULT_STEP)
        self.income_min_var = tk.StringVar(value=DEFAULT_INCOME_MIN)
        self.income_max_var = tk.StringVar(value=DEFAULT_INCOME_MAX)
        self.output_var = tk.StringVar(value=DEFAULT_OUTPUT)
        self.status_var = tk.StringVar(value="Bereit")
        self.create_btn: ttk.Button | None = None

        self._build_ui()

    def _resource_path(self, filename: str) -> Path:
        """Liefert Ressourcenpfad für Entwicklung und PyInstaller-EXE."""
        if getattr(sys, "frozen", False):
            base_path = Path(getattr(sys, "_MEIPASS", self.base_dir))
        else:
            base_path = self.base_dir
        return base_path / filename

    def _set_app_icon(self) -> None:
        """Setzt app_icon.ico als Fenster-/Anwendungsicon (Windows)."""
        icon_path = self._resource_path("app_icon.ico")
        if not icon_path.exists():
            return

        try:
            # Unter Windows in der Regel für Titelleiste + Taskleiste ausreichend.
            self.iconbitmap(default=str(icon_path))
        except Exception:
            # Keine harte Abbruchbedingung: GUI soll auch ohne Icon laufen.
            pass

    def _build_ui(self) -> None:
        root_frame = ttk.Frame(self, padding=14)
        root_frame.grid(row=0, column=0, sticky="nsew")

        ttk.Label(root_frame, text="Jahr (YYYY):").grid(row=0, column=0, sticky="w", pady=(0, 8))
        year_values = [str(year) for year in SUPPORTED_YEARS]
        year_combo = ttk.Combobox(
            root_frame,
            textvariable=self.year_var,
            values=year_values,
            state="readonly",
            width=14,
        )
        year_combo.grid(row=0, column=1, sticky="w", pady=(0, 8))
        year_combo.set(DEFAULT_YEAR)

        ttk.Label(root_frame, text="Schrittweite (EUR):").grid(row=1, column=0, sticky="w", pady=(0, 8))
        step_combo = ttk.Combobox(
            root_frame,
            textvariable=self.step_var,
            values=[str(step) for step in ALLOWED_STEPS],
            state="readonly",
            width=14,
        )
        step_combo.grid(row=1, column=1, sticky="w", pady=(0, 8))
        step_combo.set("5")

        ttk.Label(root_frame, text="Einkommen min (EUR):").grid(row=2, column=0, sticky="w", pady=(0, 8))
        income_min_entry = ttk.Entry(root_frame, textvariable=self.income_min_var, width=16)
        income_min_entry.grid(row=2, column=1, sticky="w", pady=(0, 8))

        ttk.Label(root_frame, text="Einkommen max (EUR):").grid(row=3, column=0, sticky="w", pady=(0, 8))
        income_max_entry = ttk.Entry(root_frame, textvariable=self.income_max_var, width=16)
        income_max_entry.grid(row=3, column=1, sticky="w", pady=(0, 8))

        ttk.Label(root_frame, text="Ausgabedatei / Speicherort:").grid(
            row=4,
            column=0,
            sticky="w",
            pady=(0, 8),
        )
        output_entry = ttk.Entry(root_frame, textvariable=self.output_var, width=42)
        output_entry.grid(row=4, column=1, sticky="ew", pady=(0, 8), padx=(0, 8))

        browse_btn = ttk.Button(root_frame, text="Durchsuchen…", command=self._choose_output)
        browse_btn.grid(row=4, column=2, sticky="ew", pady=(0, 8))

        button_frame = ttk.Frame(root_frame)
        button_frame.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(2, 10))
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)

        reset_btn = ttk.Button(button_frame, text="Zurücksetzen", command=self._reset_fields)
        reset_btn.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.create_btn = ttk.Button(button_frame, text="Tabelle erstellen", command=self._create_table)
        self.create_btn.grid(row=0, column=1, sticky="ew", padx=(4, 0))

        help_frame = ttk.Frame(root_frame)
        help_frame.grid(row=7, column=0, columnspan=3, sticky="ew", pady=(10, 0))
        help_frame.columnconfigure(0, weight=1)
        help_frame.columnconfigure(1, weight=1)

        user_manual_btn = ttk.Button(help_frame, text="? Anwender-Hilfe", command=self._open_user_manual)
        user_manual_btn.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        tech_docs_btn = ttk.Button(help_frame, text="? Technische Doku", command=self._open_tech_docs)
        tech_docs_btn.grid(row=0, column=1, sticky="ew", padx=(4, 0))

        status_label = ttk.Label(root_frame, textvariable=self.status_var)
        status_label.grid(row=8, column=0, columnspan=3, sticky="w")


        root_frame.columnconfigure(1, weight=1)

    def _default_filename(self, year: int) -> str:
        return get_output_filename(year)

    def _reset_fields(self) -> None:
        """Setzt alle Eingabefelder auf Standardwerte zurück."""
        self.year_var.set(DEFAULT_YEAR)
        self.step_var.set(DEFAULT_STEP)
        self.income_min_var.set(DEFAULT_INCOME_MIN)
        self.income_max_var.set(DEFAULT_INCOME_MAX)
        self.output_var.set(DEFAULT_OUTPUT)
        self.status_var.set("Eingaben zurückgesetzt")

    def _choose_output(self) -> None:
        year = self.year_var.get().strip()
        try:
            year_int = int(year)
            suggested = self._default_filename(year_int)
        except ValueError:
            suggested = "Lohnsteuer_West_monatlich.xlsx"

        file_path = filedialog.asksaveasfilename(
            title="Ausgabedatei auswählen",
            initialdir=str(Path(self.output_var.get().strip() or ".").resolve())
            if Path(self.output_var.get().strip() or ".").exists()
            else str(Path(".").resolve()),
            initialfile=suggested,
            defaultextension=".xlsx",
            filetypes=[("Excel-Datei", "*.xlsx")],
        )

        if file_path:
            self.output_var.set(file_path)

    def _resolve_output_path(self, year: int) -> Path:
        raw_output = self.output_var.get().strip()
        default_filename = self._default_filename(year)

        if raw_output in ("", "."):
            return Path(".") / default_filename

        path = Path(raw_output).expanduser()

        if path.exists() and path.is_dir():
            return path / default_filename

        if path.suffix.lower() != ".xlsx":
            if path.suffix == "":
                return path.with_suffix(".xlsx")

        return path

    def _set_busy_state(self, busy: bool) -> None:
        """Aktiviert bzw. deaktiviert die GUI während der Generierung."""
        if self.create_btn is not None:
            self.create_btn.configure(state="disabled" if busy else "normal")

    def _set_status(self, message: str) -> None:
        """Setzt den Status im UI-Thread."""
        self.status_var.set(message)
        self.update_idletasks()

    def _run_table_creation(
        self,
        *,
        year: int,
        step: int,
        income_min: float,
        income_max: float,
        output_path: Path,
    ) -> None:
        """Führt die eigentliche Erzeugung im Hintergrund-Thread aus."""
        try:
            generator = AVAILABLE_GENERATORS.get(year)
            if generator is None:
                raise RuntimeError(f"Kein Generator für Jahr {year} verfügbar.")

            self.after(
                0,
                self._set_status,
                f"Rohdaten werden berechnet… (Schrittweite: {step} EUR, Bereich: {income_min}-{income_max} EUR)",
            )
            raw_df = generator(step=step, income_min=income_min, income_max=income_max)

            self.after(0, self._set_status, "Excel-Struktur wird erstellt…")
            wide_df = build_wide_dataframe(raw_df)

            self.after(0, self._set_status, "Excel-Datei wird geschrieben…")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            write_excel_file(output_path=output_path, wide_df=wide_df, raw_df=raw_df, year=year)

            self.after(0, self._set_status, "Fertig")
            self.after(
                0,
                messagebox.showinfo,
                "Erfolg",
                f"Die Tabelle wurde erfolgreich erstellt:\n{output_path.resolve()}",
            )
        except Exception as exc:
            self.after(0, self._set_status, "Fehler")
            self.after(0, messagebox.showerror, "Fehler", f"Erstellung fehlgeschlagen:\n{exc}")
        finally:
            self.after(0, self._set_busy_state, False)

    def _create_table(self) -> None:
        year_text = self.year_var.get().strip()
        step_text = self.step_var.get().strip()
        income_min_text = self.income_min_var.get().strip().replace(",", ".")
        income_max_text = self.income_max_var.get().strip().replace(",", ".")

        try:
            year = int(year_text)
        except ValueError:
            messagebox.showerror("Ungültige Eingabe", "Bitte eine gültige Jahreszahl (YYYY) eingeben.")
            return

        try:
            step = int(step_text)
        except ValueError:
            messagebox.showerror(
                "Ungültige Eingabe",
                "Bitte eine gültige Schrittweite eingeben (3, 5, 10 oder 50 EUR).",
            )
            return

        if step not in ALLOWED_STEPS:
            messagebox.showerror(
                "Ungültige Eingabe",
                "Erlaubte Schrittweiten sind: 3, 5, 10 und 50 EUR.",
            )
            return

        try:
            income_min = float(income_min_text)
            income_max = float(income_max_text)
        except ValueError:
            messagebox.showerror(
                "Ungültige Eingabe",
                "Bitte gültige Zahlen für Einkommen min/max eingeben.",
            )
            return

        if income_min < 0 or income_max < 0:
            messagebox.showerror(
                "Ungültige Eingabe",
                "Einkommen min/max dürfen nicht negativ sein.",
            )
            return

        if income_max < income_min:
            messagebox.showerror(
                "Ungültige Eingabe",
                "Einkommen max muss größer oder gleich Einkommen min sein.",
            )
            return

        generator = AVAILABLE_GENERATORS.get(year)
        if generator is None:
            messagebox.showwarning(
                "Tarifdaten nicht verfügbar",
                (
                    f"Für {year} liegen noch keine benötigten Zahlen aus\n"
                    f"Quelle: BMF Einkommensteuer-Tarifformeln {year}\n"
                    "in diesem Projekt vor.\n\n"
                    "Die Anwendung wird nach Bestätigung geschlossen."
                ),
            )
            self.destroy()
            return

        output_path = self._resolve_output_path(year)

        self._set_busy_state(True)
        self._set_status("Generierung startet…")

        worker = threading.Thread(
            target=self._run_table_creation,
            kwargs={
                "year": year,
                "step": step,
                "income_min": income_min,
                "income_max": income_max,
                "output_path": output_path,
            },
            daemon=True,
        )
        worker.start()

    def _open_user_manual(self) -> None:
        """Öffnet die Anwender-Dokumentation (LIESMICH.TXT).
        
        Versucht zuerst, die eingebettete Dokumentation zu verwenden (für EXE),
        fällt ansonsten auf Dateisystem zurück (für Entwicklung).
        """
        # Priorität 1: Embedded Documentation (für EXE)
        if EMBEDDED_DOCS_AVAILABLE:
            try:
                readme_path = get_temp_doc_path('readme')
                self._open_doc_file(readme_path)
                return
            except Exception:
                # Fallback zu Dateisystem
                pass

        # Priorität 2: Dateisystem - ausschließlich docs/LIESMICH.TXT
        readme_path = self.base_dir.parent / "docs" / "LIESMICH.TXT"

        if not readme_path.exists():
            messagebox.showwarning(
                "Dokumentation nicht gefunden",
                f"LIESMICH.TXT existiert nicht unter:\n  {self.base_dir.parent / 'docs' / 'LIESMICH.TXT'}\n\n" +
                "Hinweis: Bei der EXE sollte die Dokumentation eingebettet sein."
            )
            return

        self._open_doc_file(readme_path)

    def _open_tech_docs(self) -> None:
        """Öffnet die Technische Dokumentation.
        
        Versucht zuerst, die eingebettete Dokumentation zu verwenden (für EXE),
        fällt ansonsten auf Dateisystem zurück (für Entwicklung).
        """
        # Priorität 1: Embedded Documentation (für EXE)
        if EMBEDDED_DOCS_AVAILABLE:
            try:
                tech_path = get_temp_doc_path('tech')
                self._open_doc_file(tech_path)
                return
            except Exception:
                # Fallback zu Dateisystem
                pass
        
        # Priorität 2: Dateisystem
        root_dir = self.base_dir.parent
        tech_docs = root_dir / "docs" / "DOKUMENTATION_TECHNIK.md"
        
        if not tech_docs.exists():
            messagebox.showwarning(
                "Dokumentation nicht gefunden",
                f"DOKUMENTATION_TECHNIK.md existiert nicht unter:\n{tech_docs}\n\n" +
                "Hinweis: Bei der EXE sollte die Dokumentation eingebettet sein."
            )
            return
        
        self._open_doc_file(tech_docs)
    
    def _open_doc_file(self, file_path: Path) -> None:
        """Öffnet eine Dokumentationsdatei mit dem Standard-Editor."""
        try:
            # Windows
            subprocess.Popen(["notepad", str(file_path)])
        except Exception:
            try:
                # macOS
                subprocess.Popen(["open", str(file_path)])
            except Exception:
                try:
                    # Linux
                    subprocess.Popen(["xdg-open", str(file_path)])
                except Exception:
                    messagebox.showerror(
                        "Fehler",
                        f"Dokumentation konnte nicht geöffnet werden.\n\nDatei: {file_path}"
                    )


def main() -> int:
    app = TaxTableGui()
    app.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
