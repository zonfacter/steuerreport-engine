# Etappe 0 – Entwurf Verzeichnisstruktur und SQLite-Schema

## Entwurf der modularen Verzeichnisstruktur

```text
src/tax_engine/
  api/                  # FastAPI Endpunkte
  core/                 # FIFO Kernlogik (ohne Ruleset-Hardcoding)
  db/                   # SQL-Schema und DB-Zugriff
  integrity/            # Golden-Hash und Integritätsprüfungen
  queue/                # persistente SQLite-Queue für 30k+ Events
  rulesets/
    de_2026/            # versioniertes deutsches Ruleset
configs/
  golden_hashes.json    # freigegebene Soll-Hashes (jahrbasiert)
docs/etappe_0/
  STRUKTUR_UND_SCHEMA_ENTWURF.md
tests/fixtures/golden/  # Golden-Case Eingänge für Integritätschecks
```

## Initiales SQLite-Schema (Auszug)

Pflichtfelder aus den Leitplanken:
- `depot_id` in `ingestion_events`, `fifo_lots` und optional in `audit_trail`
- `audit_trail` als eigene Tabelle für alle automatisierten Entscheidungen
- Auditierbarkeit jeder Berechnung über `run_id`, `config_hash`, `ruleset_version`

Siehe vollständige Definition in `src/tax_engine/db/schema.sql`.
