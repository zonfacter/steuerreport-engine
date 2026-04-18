# Steuerreport Engine (DE, ab 2020)

Modulare, auditierbare Steuer-Engine für Krypto- und Multi-Depot-Szenarien (CEX/DEX/On-Chain) mit Fokus auf deutsches Steuerrecht.

## Kernziele
- Deterministische Berechnung mit `Decimal`.
- Trennung von Core-Engine und Rulesets (pluggable Tax Rules).
- Revisionssicherheit mit Fingerprints, Integritäts-IDs und Snapshots.
- Review-first Workflow für Datenklärung, Overrides und Audit-Trace.

## Projektstruktur
- `src/tax_engine/` Anwendungscode (Core, API, Ingestion, Rulesets, Integrity)
- `tests/` Unit-, Integration- und Golden-Case-Tests
- `configs/` versionierte Konfigurationen und Ruleset-Profile
- `docs/` vollständiges technisches Dossier und Governance-Dokumente
- `scripts/` Hilfsskripte (z. B. Integritätsprüfung)
- `.github/` CI-Workflow und PR-Template

## Quick Start (lokal)
1. Python 3.11+ installieren.
2. Development-Abhängigkeiten installieren: `make install-dev`
3. Tests ausführen: `make test`
4. Integritätsprüfung starten: `make verify`
5. End-to-End Smoke-Test (ohne Serverstart): `make smoke`

## Developer Commands
- `make lint` Ruff-Checks
- `make typecheck` Mypy-Prüfung
- `make test-cov` Testlauf mit Coverage
- `make ci` lokaler CI-ähnlicher Sammellauf
- `make smoke` schneller End-to-End-Flow (Import/Reconcile/Process/Worker)

## UX-Status
- Ein erstes lokales Web-Dashboard ist verfügbar unter `GET /app`.
- Start:
  1. `cd /workspace/steuerreport`
  2. `PYTHONPATH=src uvicorn tax_engine.api:app --reload --port 8000`
  3. Browser: `http://localhost:8000/app`
- Das Dashboard deckt aktuell ab:
  - Import Confirm
  - Connector-Preview (Binance, Bitget, Coinbase, Pionex, Blockpit)
  - Reconcile Auto/Manual + Unmatched View
  - Process Run / Worker Run Next / Status
- UX-Verbesserungen (aktuell):
  - Schritt-Navigation (Import, Reconcile, Process, Review)
  - Form-Validierung und Status-/Fehlermeldungen
  - Kandidatenlisten für manuelles Transfer-Matching
  - Kennzahlen-Review für Job-Status, Tax-/Derivative-Lines
  - Review-Tabellen für `tax_lines` und `derivative_lines`
  - Filter (Asset/Status/Event-Typ) und CSV-Download direkt im Browser

## Import-Connectoren (Phase 1)
- Unterstützte Quellen (CSV/XLSX + API später): `binance`, `bitget`, `coinbase`, `pionex`, `blockpit`
- Endpunkte:
  - `GET /api/v1/import/connectors`
  - `POST /api/v1/import/parse-preview` (JSON-Rows -> kanonisches Vorschauformat)
  - `POST /api/v1/import/upload-preview` (Dateiinhalt als Base64 + Dateiname -> Vorschau)

## CEX API (Phase 2 Start)
- Read-Only-Verbindungsprüfung und Kontostands-Vorschau:
  - `POST /api/v1/connectors/cex/verify`
  - `POST /api/v1/connectors/cex/balances-preview`
- Read-Only-Transaktions-Vorschau:
  - `POST /api/v1/connectors/cex/transactions-preview`
- Direkter API-Import in `raw_events`:
  - `POST /api/v1/connectors/cex/import-confirm`
- Unterstützte CEX im ersten API-Schnitt:
  - Binance
  - Bitget (mit Passphrase)
  - Coinbase Exchange API (mit Passphrase, nicht Coinbase Advanced Trade)
- Status `transactions-preview`:
  - Binance: Deposits + Withdrawals (signierte API-Abfrage)
  - Bitget: Deposit-/Withdrawal-Records + Spot-Fills (signierte API-Abfrage)
  - Coinbase Exchange: Accounts-Ledger + Fills (signierte API-Abfrage)
- Dashboard: In Schritt 1 existiert jetzt eine CEX-Importmaske für Verify/Preview/Import ohne manuelles Copy-Paste.

## Solana / Phantom API (Phase 2)
- Wallet-Preview und Direktimport:
  - `POST /api/v1/connectors/solana/wallet-preview`
  - `POST /api/v1/connectors/solana/import-confirm`
- Funktionsumfang:
  - Signatures via `getSignaturesForAddress`
  - Transaction-Details via `getTransaction` (jsonParsed)
  - Mapping in kanonische Events (`sol_transfer`, `token_transfer`, Fallback `solana_tx`)
  - Jupiter Multi-Hop Aggregation (optional): reduziert Sub-Events auf `swap_out_aggregated` + `swap_in_aggregated`
    und ignoriert Intermediary-Tokens in der Vorschau.
  - Heuristisches DeFi-Labeling pro Transaktion/Event (`swap`, `lp`, `staking`, `claim`, `unknown`).
  - RPC-Fallbacks: bei `429/403` wird automatisch auf alternative Endpunkte gewechselt.
  - Dashboard-Maske in Schritt 1 zum direkten Testen mit Wallet-Adresse und RPC-URL

## Compliance & Qualität
- KI-4-Augen-Prinzip (entkoppelte Prompt-Generierung für Logik und Tests).
- Pflicht-Regression über Golden Cases (`DE-2024`, `DE-2025`, `DE-2026`).
- Branch Protection + Required Checks + signierte Commits.

## Dokumentation
Zentraler Dossier-Index:
- [docs/README_DOSSIER_INDEX.md](docs/README_DOSSIER_INDEX.md)

Wichtige Kern-Dokumente:
- [docs/13_MODULARE_STEUER_ENGINE.md](docs/13_MODULARE_STEUER_ENGINE.md)
- [docs/14_INTEGRITAET_VERSIONIERUNGS_KEYS.md](docs/14_INTEGRITAET_VERSIONIERUNGS_KEYS.md)
- [docs/15_GITHUB_WORKFLOW_COMPLIANCE.md](docs/15_GITHUB_WORKFLOW_COMPLIANCE.md)
