# API-Erweiterungen (für Review-First Workflow)

## 1. Zielsetzung
Die API muss neben Verarbeitung und Export explizit die manuelle Validierung, Explainability und revisionssichere Korrekturen unterstützen.

## 2. Versionierung und Konvention
- Alle Endpunkte sind kanonisch unter ` /api/v1 ` erreichbar.
- Standard-Response-Schema:
```json
{
  "trace_id": "uuid",
  "status": "success|error|partial",
  "data": {},
  "errors": [],
  "warnings": []
}
```
- Fehlerobjekt (empfohlen): `code`, `message`, `field`, `hint`.

## 3. Import und Erkennung
- `POST /api/v1/import/detect-format`
  - Zweck: Quelle, Locale-/Datumsformat und Importprofil erkennen.

- `POST /api/v1/import/normalize-preview`
  - Zweck: Normalisierungsvorschau inkl. Zahlen-/Einheitenumrechnung ohne Persistenz.

- `POST /api/v1/import/confirm`
  - Zweck: Persistiert den freigegebenen Importlauf (`source_files`, `raw_events`) mit Parser-/Faktorprofil.

- `GET /api/v1/ingest/status/{job_id}`
  - Zweck: Fortschritt der Normalisierung und Deduplizierung.

- `POST /api/v1/import/traderepublic/parse`
  - Zweck: Trade-Republic-Import mit dediziertem Mapping-Profil.

## 4. Review und Korrekturen
- `GET /api/v1/review/unmatched`
- `POST /api/v1/review/reconcile`
- `POST /api/v1/review/merge`
- `POST /api/v1/review/split`
- `POST /api/v1/review/ignore`
- `DELETE /api/v1/review/ignore/{rule_id}`
- `POST /api/v1/review/timezone-correct`
- `POST /api/v1/review/comment`
- `GET /api/v1/review/comments`

## 5. Verarbeitung und Runs
- `POST /api/v1/process/run`
  - Zweck: Berechnung starten (optional `dry_run=true`, `ruleset_version`, `year`, `fifo_mode`, `scope_strategy`).
  - Lauf wird in persistenter SQLite-Queue gestartet.

- `GET /api/v1/process/status/{job_id}`
  - Zweck: Fortschritt und Teilstände inkl. Warnungen.

- `POST /api/v1/process/finalize/{run_id}`
  - Zweck: Dry-Run als finalen persistierten Run festschreiben.

## 6. Audit und Explainability
- `GET /api/v1/audit/trace/{tax_line_id}`
- `GET /api/v1/audit/run/{run_id}`
- `GET /api/v1/audit/trace-document/{run_id}`
- `GET /api/v1/audit/sample`
- `GET /api/v1/audit/transfer-chain/{transfer_chain_id}`

## 7. Reporting
- `GET /api/v1/report/export`
  - Zweck: CSV/JSON/PDF erzeugen (PDF-Splitting bei >100 Seiten).

- `GET /api/v1/report/files/{run_id}`

## 8. Klassifikation und Compliance
- `GET /api/v1/compliance/classification`
  - Zweck: Ampelstatus zur möglichen gewerblichen Einstufung.

- `GET /api/v1/compliance/classification/{run_id}`
  - Zweck: Laufbezogene Auswertung mit reproduzierbaren Parametern.

- `GET /api/v1/compliance/business-indicator/{run_id}`
- `GET /api/v1/compliance/mismatch`
- `GET /api/v1/compliance/elster/preview`

## 9. Helium- und Smart-Cleaning
- `POST /api/v1/helium/rewards/revalue`
- `GET /api/v1/helium/classification/status`
- `POST /api/v1/helium/classification/override`
- `POST /api/v1/helium/migration/bridge`
- `POST /api/v1/ingest/classify`
- `POST /api/v1/reconcile/adjustments`

## 10. Depot-Separation
- `GET /api/v1/depots`
- `POST /api/v1/depots`
- `PATCH /api/v1/depots/{depot_id}`
- `POST /api/v1/transfers/confirm-internal`

## 11. OptimizationEngine
- `POST /api/v1/optimization/suggestions`
- `POST /api/v1/optimization/simulate`

## 12. Ruleset-Management
- `GET /api/v1/rulesets`
- `POST /api/v1/rulesets`
- `GET /api/v1/rulesets/{ruleset_id}/{ruleset_version}`
- `POST /api/v1/process/compare-rulesets`
  - Zweck: Side-by-Side-Berechnung für ein identisches Dataset mit zwei Rulesets.

## 13. Integrität und Snapshots
- `GET /api/v1/integrity/report/{run_id}`
- `GET /api/v1/integrity/event/{unique_event_id}`
- `POST /api/v1/snapshots/create/{run_id}`
- `GET /api/v1/snapshots/{snapshot_id}`

## 14. API-Qualitätsregeln
- Alle mutierenden Endpunkte schreiben Audit-Events.
- Alle Overrides sind reversibel.
- Alle Responses folgen dem Standard-Response-Schema.
- Fehler sind kategorisiert (`validation_error`, `data_gap`, `conflict`, `internal_error`).
