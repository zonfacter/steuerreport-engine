# Daten-Integrität und Versionierungs-Keys (Chain of Trust)

## 1. Zielsetzung
Jede Änderung an Daten, Konfiguration oder Ruleset muss kryptografisch nachvollziehbar sein.

## 2. Data-Fingerprint (Input-Hash)
- Beim ersten Persistieren erhält jedes Event eine `unique_event_id`.
- Bildung über kanonisierte Rohdatenfelder, z. B.:
  - Datum/Zeit,
  - Asset,
  - Menge,
  - TxID,
  - Depot,
  - Quelle.
- Kleinste Quelländerung führt zu anderer Fingerprint-ID.

## 3. Calculation-Fingerprint (Report-Integritäts-ID)
Für jeden Run/Report wird ein Master-Fingerprint gebildet aus:
- `data_hash` (kombinierter Hash aller einbezogenen Events),
- `ruleset_hash` (ID+Version+Manifest),
- `config_hash` (relevante Laufparameter).

Ergebnis:
- `report_integrity_id` als eindeutige, prüfbare Integritätskennung.

## 4. Änderungsworkflow und Statusmodell
Wenn sich Daten nach Finalisierung ändern:
- Neuer `override_id`/neue Version statt Überschreiben.
- Vorheriger Reportstatus wird auf `DIRTY` oder `OUTDATED` gesetzt.
- `version_history` dokumentiert Kette, z. B. `V1(KeyA) -> V2(KeyB)`.

## 5. Snapshot-Funktion
- Bei Report-Finalisierung wird ein Snapshot (logisch oder physisch) erstellt.
- Snapshot enthält Datenzustand, Ruleset-Metadaten und Konfiguration.
- Ziel: Reproduktion historischer Berechnungen auch bei späteren Systemänderungen.

## 6. Sichtbarkeit im Export/PDF
- `report_integrity_id` wird auf jeder PDF-Seite angezeigt.
- Optional zusätzlich QR-Code mit Verweis auf Integritätsmetadaten.

## 7. API-Anforderungen
- `GET /api/v1/integrity/report/{run_id}`
- `GET /api/v1/integrity/event/{unique_event_id}`
- `POST /api/v1/snapshots/create/{run_id}`
- `GET /api/v1/snapshots/{snapshot_id}`

## 8. Datenmodell-Erweiterungen
- `event_fingerprints`
  - `unique_event_id`, `source_event_ref`, `hash_algo`, `canonical_payload_hash`
- `report_integrity`
  - `run_id`, `data_hash`, `ruleset_hash`, `config_hash`, `report_integrity_id`
- `version_history`
  - `entity_type`, `entity_id`, `prev_version`, `new_version`, `reason`, `changed_at`
- `snapshots`
  - `snapshot_id`, `run_id`, `storage_ref`, `created_at`, `checksum`

## 9. Sicherheitsanforderungen
- Hashing mit kryptografisch sicherem Verfahren (z. B. SHA-256 oder stärker).
- Fingerprints werden nicht mutiert, nur ergänzt.
- Integritätsprüfungen sind Teil der CI- und Run-Validierung.

## 10. Verifikation
- Re-Import unveränderter Daten reproduziert identische `unique_event_id`.
- Geänderte Daten erzeugen unterschiedliche Fingerprints.
- Report-Integritäts-ID ändert sich bei jeder relevanten Änderung an Daten, Ruleset oder Config.
