# Draft Export Notice Embedding - 2026-05-09

## Ergebnis

Solange der Pionex/USDT-Review-Blocker offen ist, markieren die Export-Artefakte sich jetzt selbst als Entwurf.

Betroffener Blocker:

- Kandidat: `pionex-usdt-opening-balance-2021-12-28`
- Status: `needs_evidence`
- Gate: finaler Export gesperrt, Entwurfsnutzung mit Hinweis erlaubt

## Umsetzung

- JSON-Export:
  - `data.draft_notice`
  - erste Exportzeile `line_type=draft_notice`
- CSV-Export:
  - zusaetzliche Spalten `notice_code`, `notice_message`, `notice_candidate_id`, `notice_required_evidence`
  - erste Datenzeile `draft_notice`
- WISO-CSV:
  - erste Headerzeile enthaelt `Draft_Status:NOT_FINAL`, `Draft_Blocker:...`, `Draft_Candidate:...`
- PDF:
  - oberer Seitenbereich zeigt `ENTWURF - NICHT FINAL`, Blocker-Hinweis und Belegbedarf
- Report-Dateiliste:
  - Labels werden mit `ENTWURF - ...` gepraegt
  - jede Datei enthaelt `draft_notice`

## Aktualisierte lokale Exporte

`var/report_exports_current_2026-05-09/` wurde neu geschrieben. Es wurden `22` Exportdateien aktualisiert.

Beispiel 2023:

- `var/report_exports_current_2026-05-09/2023_c8065ea8-d697-4721-8873-d091478b5341_all.json`
- `var/report_exports_current_2026-05-09/2023_c8065ea8-d697-4721-8873-d091478b5341_tax.csv`
- `var/report_exports_current_2026-05-09/2023_c8065ea8-d697-4721-8873-d091478b5341_wiso.csv`

## Tests

- `python3 -m py_compile src/tax_engine/api/processing.py src/tax_engine/api/reporting.py`
- `PYTHONPATH=src pytest -q tests/unit/api/test_api_coverage_gate.py::test_report_export_marks_draft_when_balance_candidate_blocks_gate tests/unit/api/test_api_coverage_gate.py::test_report_export_integrity_snapshot_and_compliance_paths`
- Live Port `8000`:
  - JSON enthaelt `draft_notice`
  - CSV beginnt mit `draft_notice`
  - WISO-CSV Header enthaelt `Draft_Status:NOT_FINAL`
  - PDF liefert gueltige PDF-Daten
