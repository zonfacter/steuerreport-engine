# 2025 Export-Paket Validierung

Stand: 2026-05-11

## Scope

Validiert wurde der neue 2025-Job nach der Bitget-Derivate-Neuberechnung:

```text
job_id=b7c013f5-d176-4875-bdbe-df614bee4800
tax_year=2025
status=completed
tax_lines=465
derivative_lines=957
```

Die Export-Artefakte wurden lokal unter `var/export_validation_2025_derivatives_2026-05-11/`
erzeugt. Dieser Ordner bleibt lokal und wird nicht committed.

## Export-Dateien

Die Report-API liefert `11` Dateien:

| Scope | Format | Zeilen | PDF-Teile |
| --- | --- | ---: | ---: |
| all | JSON | 1442 | - |
| all | CSV | 1442 | - |
| all | WISO | 465 | - |
| all | PDF | 1442 | 1 |
| tax | JSON | 485 | - |
| tax | CSV | 485 | - |
| tax | WISO | 465 | - |
| tax | PDF | 485 | 1 |
| derivatives | JSON | 957 | - |
| derivatives | CSV | 957 | - |
| derivatives | PDF | 957 | 1 |

Der Vollreport enthaelt:

```text
tax_domain_summary=20
tax=465
derivative=957
```

CSV-Dateizeilen inklusive Header:

```text
all.csv=1443
tax.csv=486
derivatives.csv=958
wiso.csv=409
```

## PDF-Seitenlimit

Alle PDFs liegen deutlich unter der harten Grenze von `100` Seiten je Datei:

| PDF | Seiten | Teile |
| --- | ---: | ---: |
| all | 52 | 1/1 |
| tax | 18 | 1/1 |
| derivatives | 36 | 1/1 |

Der Abruf von `part=2` fuer alle drei PDF-Scopes liefert korrekt:

```text
report_part_not_found
part_count=1
```

Damit ist die PDF-Splitting-/Seitenlimit-Logik fuer den aktuellen 2025-Job plausibel.

## WISO

Der WISO-Steuer-CSV-Export fuer `scope=tax` wurde erzeugt. Header:

```text
Identifier:Capital_Gains,Method:FIFO,Tax_Year:2025,Base_Currency:EUR,Par22Nr3:0
Amount,Currency,Date Acquired,Date Sold,Short / Long,Buy / Input at,Sell / Output at,Proceeds,Cost Basis,Gain / Loss
```

Hinweis: Der WISO-Export bildet Tax-Lines ab. Derivate werden separat im
Derivate-CSV/PDF-Scope gefuehrt und in der steuerlichen Zusammenfassung als
Termingeschaefte ausgewiesen.

## Review-Gate

Job-spezifisches Review-Gate:

```text
allow_export=true
blocking_reasons=[]
warning_reasons=[]
issues_open=0
issues_open_total=3
issues_historical_open=3
issues_high_open=0
unmatched_total=0
final_export_allowed=true
```

## Ergebnis

Das 2025 Export-Paket ist technisch plausibel:

- Tax- und Derivate-Zeilen sind im Vollreport enthalten.
- Derivate haben eigene JSON/CSV/PDF-Exports.
- WISO-CSV fuer Tax-Lines wird erzeugt.
- PDF-Dateien bleiben unter `100` Seiten.
- Unzulaessige PDF-Parts werden korrekt abgewiesen.
- Review-Gate erlaubt finalen Export fuer den 2025-Job.

Keine steuerberaterliche Endfreigabe; es handelt sich um den technischen
Export- und Plausibilitaetsstand des Projekts.
