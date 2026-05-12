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
- `GET /api/v1/review/negative-balances`
  - Zweck: Negative kumulierte Asset-Bestaende je Stichtag oder Jahr als Review-Issues ausgeben.
  - Query: `as_of=YYYY-MM-DD` fuer einen Stichtag oder `year=2025` fuer Monatsmarken eines Steuerjahres, optional `asset`, `limit`, `include_events`.
  - Response: `issue_id`, `status`, `severity`, `date`, `asset`, `balance`, `price_usd`, `value_usd`, `first_negative_at_utc`, `event_counts`, `source_breakdown`, `last_event`, `recent_events`.
  - Bearbeitung per API: `POST /api/v1/issues/update-status`, `POST /api/v1/review/comment`, `POST /api/v1/review/ignore`, `POST /api/v1/review/merge`, `POST /api/v1/review/split`, `POST /api/v1/tax/event-override/upsert`.
- `GET /api/v1/review/issue-context/{issue_id}`
  - Zweck: Maschinenlesbarer Kontext fuer KI-/ML-Review ohne Voll-Dump aller Rohdaten.
  - Fuer `negative_balance:<YYYY-MM-DD>:<ASSET>` liefert der Endpunkt Issue, Asset-Jahressummen, Kontext-Events mit laufendem Saldo, gleiche Transaktions-Events und einen `analysis_contract`.
  - Query: optional `window_days` und `limit`.
- `POST /api/v1/ai/review/analyze`
  - Zweck: KI-/ML-kompatiblen Review-Vorschlag aus `issue-context` erzeugen und optional speichern.
  - Input: `issue_id`, `persist`, `window_days`, `limit`, `engine`.
  - Output: `suggestion_id`, Prioritaet, Confidence, vermutete Ursache, Evidenz-Event-IDs, offene Datenfragen, empfohlene API-Aktionen.
  - Engine `deterministic-v1`: lokaler deterministischer Fallback ohne LLM.
  - Engine `ollama`: nutzt Runtime-Settings `runtime.ai_review.ollama_base_url`, `runtime.ai_review.ollama_model`, `runtime.ai_review.ollama_timeout_seconds`, `runtime.ai_review.ollama_temperature`, `runtime.ai_review.ollama_num_ctx`.
  - Aktuelles Zielsetup: CT203 `http://192.168.2.203:11434` mit `qwen2.5:14b`.
- `GET /api/v1/ai/review/suggestions`
  - Zweck: Gespeicherte Vorschlaege nach `issue_id`/`status` abrufen.
- `POST /api/v1/ai/review/apply-suggestion`
  - Zweck: Nur sichere Aktionen anwenden (`set_status`, `comment_last_event`); Merge/Split/Ignore/Tax-Override bleiben bestaetigungspflichtig.
- `POST /api/v1/review/reconcile`
- `POST /api/v1/review/merge`
- `POST /api/v1/review/split`
- `POST /api/v1/review/ignore`
- `GET /api/v1/review/gates`
  - Zweck: Export-/Report-Gates pruefen.
  - Blockiert bei unmatched Transfers, offenen High-Severity-Issues und Review-only Balance-Adjustment-Kandidaten mit Status `needs_evidence` oder `ready_for_explicit_review_decision`.
  - Response enthaelt `counts.balance_adjustment_candidates_open` und `balance_adjustment_candidates[]` mit `candidate_id`, `platform`, `asset`, `quantity_delta`, `status`, `tax_effective=false` und letzter `review_decision`.
- `POST /api/v1/tax/event-override/delete`
- `GET /api/v1/review/exclusion-reasons`
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

## 5a. Dashboard und Plattform-Ledger
- `GET /api/v1/platform-ledger/status`
  - Zweck: Chronologische Plattform-Simulation, Transferabgleich, priorisierte Bruchstellen und KI-Hypothesen maschinenlesbar fuer Dashboard und Review liefern.
  - Response-Felder: `summary`, `transfers`, `simulation`, `transfer_candidates`, `break_resolution`, `residual_review`, `ai_review`, `files`.
  - `break_resolution.rows` bleibt die vollstaendige Bruchstellenliste.
  - `break_resolution.active_rows` enthaelt nur echte offene Blocker nach Abzug dokumentierter Restfaelle.
  - `break_resolution.documented_rows` enthaelt Restfaelle, die im Residual-Audit als `documented_rounding_dust` oder `documented_platform_context_residual` bewertet wurden.
  - `active_blocker_count` und `documented_residual_count` muessen im Dashboard getrennt dargestellt werden, damit Rundungs-/Plattformreste nicht wie steuerwirksame Blocker erscheinen.
  - `residual_review` spiegelt `var/platform_residual_review_audit_2026-05-09.json`; daraus darf kein automatischer steuerwirksamer Import abgeleitet werden.

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
- `GET /api/v1/regulatory/dac8-carf/context`
  - Zweck: Verifizierten DAC8/CARF-Kontext maschinenlesbar fuer KI-/Review-Prompts bereitstellen.
  - Quelle fuer Regeln: `docs/20_DAC8_CARF_REGELWERK.md`.
  - Status: implementiert; wird zusaetzlich in `GET /api/v1/review/issue-context/{issue_id}` unter `context.regulatory_context` eingebettet.
  - Muss unterscheiden zwischen Datensammlung ab `2026-01-01`, erstem Reportingjahr `2026` und erstem Austausch/ersten Meldungen `2027` mit EU-Frist bis `2027-09-30`.
  - Deutschland/KStTG: `de_ksttg_effective_from=2025-12-24`, Due-Diligence-Frist fuer bestehende Nutzerbeziehungen `2027-01-01`.
  - Darf DAC8/CARF-Daten nur als Referenz-/Plausibilitaetsdaten kennzeichnen, nicht als steuerliches Ergebnis.

## 9. Helium- und Smart-Cleaning
- `POST /api/v1/helium/rewards/revalue`
- `GET /api/v1/helium/classification/status`
- `POST /api/v1/helium/classification/override`
- `POST /api/v1/helium/migration/bridge`
- `POST /api/v1/ingest/classify`
- `POST /api/v1/reconcile/adjustments`

### Review-only Balance Adjustment Candidates

- `GET /api/v1/review/balance-adjustment-candidates`
- `POST /api/v1/review/balance-adjustment-candidates/upsert`
- `POST /api/v1/review/balance-adjustment-candidates/decide`
- `POST /api/v1/review/balance-adjustment-candidates/delete`

Diese Endpunkte speichern nur Review-Kandidaten und Review-Entscheidungen, keine steuerwirksamen Buchungen. `tax_effective` bleibt serverseitig `false`; eine spätere Überführung in echte Adjustment-/Importdaten muss explizit erfolgen und belegbar dokumentiert werden.

`POST /api/v1/review/balance-adjustment-candidates/decide` erlaubt nur dokumentierte Entscheidungen:

- `approve_non_tax_inventory_normalization`
- `reject_candidate`
- `request_more_evidence`

Beispiel fuer Pionex-Opening:

```json
{
  "candidate_id": "pionex-usdt-opening-balance-2021-12-28",
  "decision": "approve_non_tax_inventory_normalization",
  "reviewer": "user",
  "note": "Explizite fachliche Freigabe als nicht steuerwirksame Inventar-Normalisierung; Primaer-Snapshot fehlt weiterhin.",
  "evidence": {
    "decision_dossier": "docs/157_PIONEX_OPENING_DECISION_DOSSIER_2026-05-09.md",
    "tron_audit": "docs/50_TRON_PIONEX_DEPOSIT_ADDRESS_AUDIT_2026-05-08.md"
  }
}
```

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
