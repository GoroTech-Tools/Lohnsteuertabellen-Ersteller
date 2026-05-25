"""Lokaler Pandas-Hook als stabiler Fallback für PyInstaller.

Nutzen:
- umgeht Probleme in bestimmten Versionen des Standard-Hooks
- sammelt trotzdem Submodule und Daten für die Laufzeit
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

hiddenimports = collect_submodules("pandas")
datas = collect_data_files("pandas")
