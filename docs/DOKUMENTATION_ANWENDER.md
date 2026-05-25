# Anwenderdokumentation – Lohnsteuertabellen-Ersteller

Diese Dokumentation richtet sich an Anwenderinnen und Anwender der Anwendung.

## Schnellstart

1. Anwendung starten (`tax_table_gui.py` oder EXE).
2. Jahr auswählen.
3. Schrittweite (3, 5, 10 oder 50) festlegen.
4. Einkommensbereich eingeben.
5. Ausgabepfad wählen.
6. „Tabelle erstellen“ klicken.

## Eingabefelder

| Feld | Bedeutung |
| --- | --- |
| Jahr | Unterstütztes Steuerjahr |
| Schrittweite | Abstufung in EUR |
| Einkommen min/max | Untere/obere Grenze für die Tabellenwerte |
| Ausgabedatei | Zielordner oder Dateiname (`.xlsx`) |

## Ergebnis

Die Anwendung erzeugt eine Excel-Datei mit:

- einem kompakten Übersichtsblatt
- einem Rohdatenblatt mit den berechneten Details

## Hinweise

- Die Berechnung orientiert sich an BMF/PAP-Daten.
- Für amtliche Einzelfälle immer die offiziellen Quellen prüfen.
- Bei ungültigen Eingaben zeigt die Anwendung eine klare Fehlermeldung.

## Support

- Technische Details: `docs/DOKUMENTATION_TECHNIK.md`
- Berechnungsdetails: `docs/DOKUMENTATION_KALKULATION.md`

---

**Version:** 1.2.0  
**Stand:** 25.05.2026  
**Autor:** GoroTech
