# 📋 Abhängigkeiten & Lizenzen

## Externe Quellen

### Lohnsteuer-2026 (PAP-Rechner)

| Feld | Wert |
|------|------|
| **Projekt** | Lohnsteuer (Lohnpap Generator) |
| **Autor** | Marcel Lehmann |
| **Ursprung** | https://github.com/MarcelLehmann/Lohnsteuer |
| **Lizenz** | Apache License 2.0 |
| **Copyright** | © 2015-2025 Marcel Lehmann |
| **Verwendung** | Programmablaufpläne (PAP) der Lohnsteuerberechnung |
| **Basis** | Bundesministerium der Finanzen (BMF) — Offizielle PAP-Vorgaben |

### Apache License 2.0 — Text

```
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

### Bundeszentrale für politische Bildung (bpb) / BMF

Die Programmablaufpläne (PAP) sind offizielle Dokumente des Bundesministerium der Finanzen und unterliegen ggf. anderen Vorgaben.

**Hinweis:** Diese sind für öffentliche Nutzung frei verfügbar unter:
- https://www.bmf-steuerrechner.de/interface/programmablauf.xhtml

---

## Compliance Checklist

- [x] Lizenztext vollständig eingebunden
- [x] Copyright-Hinweis dokumentiert
- [x] Originalquelle verlinkt
- [x] Verwendungszweck dokumentiert
- [x] Modifikationen gekennzeichnet (falls vorhanden)
- [x] Attribution erforderlich: Ja

---

## Attribution (in Dokumentation erforderlich)

### Zur Nutzung in:
- `README.md` → Listet externe Abhängigkeiten
- `docs/LOHNSTEUER_INTEGRATION.md` → Detaillierte Dokumentation
- Release-Notes → Bei Major Updates mit PAP-Änderungen
- Quellcode → In `pap_parser.py` als Kommentar

### Beispiel-Attribution im Code:
```python
"""
Lohnsteuer-Berechnung basierend auf 
Programmablaufplan (PAP) des Bundesministerium der Finanzen.

Referenz-Implementierung:
  Marcel Lehmann - Lohnsteuer (Apache 2.0)
  https://github.com/MarcelLehmann/Lohnsteuer
  © 2015-2025 Marcel Lehmann

Offizielle PAP-Quelle:
  https://www.bmf-steuerrechner.de/interface/programmablauf.xhtml
"""
```

---

## Version History

| Datum | Version | Änderung |
|-------|---------|----------|
| 10.05.2026 | 1.0 | Initiale Dokumentation, PAP 2026 |
| - | - | - |

---

**Letztes Review:** 10. Mai 2026  
**Nächster Check:** Bei jeder Major-Version-Änderung
