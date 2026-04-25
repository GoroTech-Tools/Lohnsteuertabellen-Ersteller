# Kalkulationsgrundlagen – Lohnsteuertabelle 2026

**Rechtsgrundlage:** § 32a EStG in der Fassung ab Veranlagungszeitraum 2026  
**Quelle Tarifformeln:** BMF-Programmablaufplan 2026 (Anlage 2), veröffentlicht 12.11.2025  
**Gültig ab:** 1. Januar 2026

---

## 1. Einkommensteuertarif (§ 32a Abs. 1 EStG 2026)

Die tarifliche Einkommensteuer wird auf das zu versteuernde Jahreseinkommen (zvE) angewendet, das auf den vollen Euro-Betrag **abgerundet** wird.

### Tarifzonen und Formeln

| Zone | zvE-Bereich | Formel |
| ---- | ----------- | ------ |
| 1 – Nullzone | ≤ 12.348 € | **S = 0** |
| 2 – 1. Progressionszone | 12.349 € – 17.799 € | **S = (914,51 · y + 1.400) · y** |
| 3 – 2. Progressionszone | 17.800 € – 69.878 € | **S = (173,10 · z + 2.397) · z + 1.034,87** |
| 4 – Proportionalzone 42 % | 69.879 € – 277.825 € | **S = 0,42 · x − 11.135,63** |
| 5 – Spitzensteuersatz 45 % | ab 277.826 € | **S = 0,45 · x − 19.470,38** |

### Hilfsvariablen

| Variable | Definition |
| -------- | ---------- |
| `y` | Zehntausendstel des den Grundfreibetrag übersteigenden Teils: `y = (zvE − 12.348) / 10.000` |
| `z` | Zehntausendstel des 17.799 € übersteigenden Teils: `z = (zvE − 17.799) / 10.000` |
| `x` | Das zvE selbst (auf vollen Euro abgerundet) |

> **Hinweis:** Die Division durch 10.000 dient ausschließlich dazu, zu viele Nachkommastellen bei den Koeffizienten zu vermeiden. Sie hat keine sachliche Bedeutung.

---

## 2. Freibeträge und Abzüge

Aus dem Jahresbruttoentgelt werden vor Anwendung der Tarifformel folgende Beträge abgezogen (sofern die Steuerklasse sie gewährt):

| Abzug | Betrag | Rechtsgrundlage | Steuerklassen |
| ----- | ------ | --------------- | ------------- |
| Arbeitnehmer-Pauschbetrag | 1.230 €/Jahr | § 9a Satz 1 Nr. 1a EStG | SK 1, 2, 3, 4 |
| Sonderausgaben-Pauschbetrag | 36 €/Jahr | § 10c EStG | alle SK |
| Vorsorgepauschale (vereinfacht) | variabel | § 39b EStG | SK 1, 2, 3, 4, 5 |
| Entlastungsbetrag Alleinerziehende | 4.260 €/Jahr | § 24b EStG | SK 2 |

---

## 3. Vorsorgepauschale (vereinfachtes Modell)

Die Vorsorgepauschale wird als Summe der Arbeitnehmeranteile zur gesetzlichen Sozialversicherung berechnet (West, 2026):

| Versicherungszweig | AN-Beitragssatz | Beitragsbemessungsgrenze |
| ------------------ | --------------- | ------------------------ |
| Rentenversicherung | 9,30 % | 89.400 €/Jahr |
| Krankenversicherung (inkl. Zusatzbeitrag ~1,6 %) | 8,15 % | 66.150 €/Jahr |
| Pflegeversicherung | 1,80 % | 66.150 €/Jahr |

**Formel:**

```text
VSP = min(Brutto, BBG_RV) × 9,30 %
    + min(Brutto, BBG_KV) × 8,15 %
    + min(Brutto, BBG_KV) × 1,80 %
```

> **Vereinfachung:** Der vollständige BMF-PAP berechnet die Vorsorgepauschale in mehreren Schritten mit Mindest- und Höchstbeträgen sowie einem Günstigkeitsvergleich. Das hier verwendete Modell summiert lediglich die AN-Anteile direkt, was für den typischen GKV-Arbeitnehmer eine gute Näherung darstellt.

---

## 4. Steuerklassen-spezifische Berechnung

### Ermittlung des zvE je Steuerklasse

| SK | Bezeichnung | zvE-Formel | Tarif-Besonderheit |
| -- | ----------- | ---------- | ------------------ |
| 1 | Alleinstehend | Brutto − AP − SO − VSP | Grundtarif |
| 2 | Alleinerziehend | Brutto − AP − SO − VSP − 4.260 € | Grundtarif + Entlastungsbetrag |
| 3 | Ehegatte (höheres Eink.) | Brutto − AP − SO − VSP | **Splitting:** S = 2 × Grundtarif(zvE / 2) |
| 4 | Ehegatte (ähnliches Eink.) | Brutto − AP − SO − VSP | Grundtarif |
| 5 | Ehegatte (niedrigeres Eink.) | Brutto − SO − VSP | Kein GFB, kein AP → zvE + 12.348 € als Eingabe |
| 6 | Zweitbeschäftigung | Brutto − SO | Kein GFB, kein AP, **keine VSP** → zvE + 12.348 € als Eingabe |

**Legende:** AP = Arbeitnehmer-Pauschbetrag, SO = Sonderausgaben-Pauschbetrag, VSP = Vorsorgepauschale, GFB = Grundfreibetrag

### Besonderheit SK 3 – Ehegattensplitting

Nach § 32a Abs. 5 EStG wird das zvE halbiert, der Grundtarif darauf angewendet und das Ergebnis verdoppelt. Das hat den Effekt, dass beide Ehepartner gemeinsam so besteuert werden, als würden sie je die Hälfte des Gesamteinkommens verdienen.

### Besonderheit SK 5/6 – kein Grundfreibetrag

Steuerpflichtige in SK 5 und SK 6 erhalten keinen Grundfreibetrag, da dieser bereits dem SK-3-Partner zugerechnet ist (SK 5) bzw. beim Hauptarbeitgeber (SK 6) verbraucht wird.

Implementierungstechnisch wird das zvE um den Grundfreibetrag **erhöht**, bevor es an `_grundtarif_2026()` übergeben wird – dadurch fällt die interne Nullzone der Tariffunktion heraus und Steuer wird ab dem ersten Euro berechnet.

### Besonderheit SK 6 – keine Vorsorgepauschale

Bei einer Zweitbeschäftigung (SK 6) führt der Hauptarbeitgeber die Sozialversicherungsbeiträge bereits vollständig ab. Die Vorsorgepauschale wird daher gemäß BMF-PAP mit **0** angesetzt.

---

## 5. Solidaritätszuschlag

```text
SolZ = Lohnsteuer × 5,5 %
```

Freigrenze und Milderungszone werden in diesem Modell nicht berücksichtigt (vereinfachend). In der Praxis entfällt der SolZ für die meisten Steuerpflichtigen mit geringem und mittlerem Einkommen vollständig.

---

## 6. Kirchensteuer

```text
KiSt = Lohnsteuer × 9 %     (Bayern, Baden-Württemberg: 8 %)
```

In der Tabelle wird einheitlich der Satz von **9 %** (West, ohne Bayern/BW) ausgewiesen.

---

## 7. Kinderfreibetrag (KFB)

Der KFB wird vereinfacht als **monatliche Einkommensminderung** modelliert:

```text
Reduziertes Einkommen = Brutto − KFB × 50 €/Monat
```

Tatsächlich wird der Kinderfreibetrag (je Kind: 6.672 €/Jahr für beide Elternteile) erst im Rahmen der Jahresveranlagung mit dem Kindergeld verrechnet (Günstigerprüfung). Die Tabelle zeigt daher eine Näherung für den monatlichen Lohnsteuereinbehalt.

---

## 8. Einkommensbereich und Schrittweite

| Parameter | Wert |
| --------- | ---- |
| Mindest-Brutto | 1.000 €/Monat |
| Höchst-Brutto | 10.000 €/Monat |
| Schrittweite | 5 €/Monat |
| Bezugszeitraum | Monat |
| Region | West |

---

## 9. Bekannte Vereinfachungen und Abweichungen

| Vereinfachung | Auswirkung |
| ------------- | ---------- |
| Vorsorgepauschale: direkte AN-Beitragssumme statt vollständigem BMF-PAP | Geringe Abweichung bei Grenzeinkommen; unterschätzt i. d. R. die VSP leicht |
| SolZ ohne Freigrenze/Milderungszone | SolZ wird bei niedrigen Einkommen ggf. zu hoch ausgewiesen |
| KFB als pauschale Einkommensminderung | Nur Näherungswert; echte Günstigerprüfung erfolgt im Jahresausgleich |
| Kirchensteuer einheitlich 9 % | In Bayern und BW gilt 8 %; keine individuelle Konfessionsauswahl |
| Keine Berücksichtigung von Altersentlastungsbetrag, Versorgungsfreibetrag etc. | Tabelle gilt für reguläre Arbeitnehmer ohne Versorgungsbezüge |

---

## 10. Build- und Release-Artefakte

Nach jedem erfolgreichen Build (`src/build_exe.py`) werden automatisch folgende Artefakte erzeugt:

- `dist/Lohnsteuertabellen-Ersteller.exe`
- `release/Lohnsteuertabellen-Ersteller_<Version>.zip`

Das ZIP-Paket enthält:

- die aktuelle EXE
- das komplette Verzeichnis `docs/` (inkl. dieser Datei)
