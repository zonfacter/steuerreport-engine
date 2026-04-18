# Changelog

Alle relevanten Änderungen an Architektur, Regeln, Integrität und Workflows werden hier dokumentiert.

## [Unreleased]
### Added
- Projektstruktur mit `src/`, `tests/`, `configs/`, `docs/`, `scripts/` erstellt.
- Dokumentationsdossier nach `docs/` konsolidiert.
- GitHub-konformes Root-README erstellt.
- `15_GITHUB_WORKFLOW_COMPLIANCE.md` als Governance-Dokument integriert.
- CI- und PR-Compliance-Struktur unter `.github/` vorbereitet.
- Python-Projektkonfiguration über `pyproject.toml` ergänzt.
- Dependency-Dateien `requirements.txt` und `requirements-dev.txt` ergänzt.
- `Makefile` mit Standard-Developer-Targets ergänzt (`lint`, `typecheck`, `test-cov`, `verify`, `ci`).
- Integritäts-Skript-Stub `scripts/verify_integrity.py` ergänzt.
- Modulare Ruleset-Strategie (`TaxRuleset`, Registry, DE-Standardregel) implementiert.
- Deterministische Integritäts-Fingerprints für Event/Config/Ruleset/Report ergänzt.
- Etappe-1-Importendpunkte ergänzt:
  - `POST /api/v1/import/detect-format`
  - `POST /api/v1/import/normalize-preview`
  - `POST /api/v1/import/confirm`
- Ingestion-Pipeline mit Decimal-/Datetime-Parsing, Subunit-Umrechnung und Audit-Trail ergänzt.
- Unit-Tests für Ruleset, Integrität, Parser und Importendpunkte ergänzt.
- Persistente SQLite-Importspeicherung ergänzt (`source_files`, `raw_events`, `audit_trail`).
- Schema-Migration `migration_v1.sql` für Etappe-1-Import-Persistenz ergänzt.
- Prozess-Queue-Endpunkte ergänzt:
  - `POST /api/v1/process/run`
  - `GET /api/v1/process/status/{job_id}`
- SQLite-Queue-Tabelle `processing_queue` inkl. Job-Lifecycle-Basis ergänzt.
- Queue-Service und Unit-Tests für Run/Status ergänzt.
- Worker-Endpoint ergänzt:
  - `POST /api/v1/process/worker/run-next`
- Job-Lifecycle erweitert: `queued -> running -> completed/failed` mit `current_step` und `error_message`.
- Worker verarbeitet jetzt echte Eventdaten aus `raw_events` und erzeugt `result_summary` pro Job.
- Queue-Persistenz erweitert um `result_json` (im Status als `result_summary` sichtbar).
- Deque-basierte FIFO-Spot-Engine mit `Decimal` implementiert (inkl. Buy/Sell-Fee-Handling).
- Persistenz für berechnete `tax_lines` pro Job ergänzt.
- Worker speichert nun neben Summary auch FIFO-Tax-Lines in SQLite.
- Unit-Tests für FIFO-Matching, Haltedauer und Short-Sell-Fallback ergänzt.

### Changed
- Doku-Referenzen auf `docs/`-Pfadstruktur umgestellt.
- CI-Workflow installiert Dev-Abhängigkeiten aus `requirements-dev.txt` (Fallback auf `requirements.txt`).
- API-Health-Test auf stabilen Contract-Test umgestellt.
- Ingestion-Store von In-Memory auf SQLite umgestellt (Standardpfad: `/tmp/steuerreport/steuerreport.db`).
