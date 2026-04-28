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

## Datenbank-Sicherheit
- Standard-DB: `~/.local/share/steuerreport/steuerreport.db`
- Test-DB: `/tmp/steuerreport/steuerreport_test.db`
- `reset_for_tests()` ist hart gesperrt und läuft nur mit `STEUERREPORT_ENV=testing`.
- Für echte Daten keine manuelle Test-Env setzen und keine Produktiv-DB unter `/tmp` betreiben.

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
  - Admin-Einstellungen mit Untermenüs (Runtime, Credentials, Security, Raw Settings)
  - Portfolio-Übersicht (Historie, Asset-Bestände, Rollen-Erkennung privat/gewerblich)
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
  - `POST /api/v1/connectors/solana/rpc-probe`
  - `POST /api/v1/connectors/solana/balance-snapshot`
  - `POST /api/v1/connectors/solana/group-balance-snapshot`
  - `POST /api/v1/connectors/solana/wallet-preview`
  - `POST /api/v1/connectors/solana/import-confirm`
  - `POST /api/v1/connectors/solana/group-import-confirm`
- Funktionsumfang:
  - Signatures via `getSignaturesForAddress`
  - Transaction-Details via `getTransaction` (jsonParsed)
  - Mapping in kanonische Events (`sol_transfer`, `token_transfer`, Fallback `solana_tx`)
  - Jupiter Multi-Hop Aggregation (optional): reduziert Sub-Events auf `swap_out_aggregated` + `swap_in_aggregated`
    und ignoriert Intermediary-Tokens in der Vorschau.
  - Heuristisches DeFi-Labeling pro Transaktion/Event (`swap`, `lp`, `staking`, `claim`, `unknown`).
  - RPC-Fallbacks: bei `429/403` und typischen RPC-Node-Fehlern wird automatisch auf alternative Endpunkte gewechselt.
  - `getTransaction` nutzt mehrere Parameter-Varianten (`jsonParsed` mit/ohne `maxSupportedTransactionVersion`, danach `json`),
    um `null`-Payloads bei unterschiedlichen RPC-Implementierungen zu reduzieren.
  - Dashboard-Maske in Schritt 1 zum direkten Testen mit Wallet-Adresse und RPC-URL
  - Balance-Snapshot unterstützt optional Preisanreicherung (`include_prices=true`):
    - primär Jupiter Price API
    - Fallback für SOL über CoinGecko (wenn Jupiter-DNS/Rate-Limit blockiert)

Empfohlene RPC-Reihenfolge für Tests/Beta:
1. Anbieter-Key-RPC (z. B. Helius/Alchemy/QuickNode/GetBlock/Chainstack)
2. `https://api.mainnet-beta.solana.com`
3. `https://api.mainnet.solana.com`
4. `https://solana-rpc.publicnode.com`
5. `https://solana.publicnode.dev`
6. `https://solana.api.pocket.network`
7. `https://solana.rpc.subquery.network/public` (nur als letzter Fallback)

No-Account-Endpoints (technisch geprüft am 2026-04-19, via `getBlockHeight`):
- funktional: `api.mainnet-beta`, `api.mainnet`, `solana-rpc.publicnode.com`, `solana.publicnode.dev`, `solana.api.pocket.network`
- nicht funktional im Test: `rpc.ankr.com/solana` (403/API-Key nötig), `solana.drpc.org` (Free-Tier blockiert Methoden), `solana.api.onfinality.io/public` (429 ohne Key), `llamarpc.com` (kein direkter Solana JSON-RPC), `solana.rpc.subquery.network/public` (500)

Konfigurierbarkeit ohne Codeänderung:
- `SOLANA_RPC_URL` setzt den Primärendpunkt.
- `SOLANA_RPC_FALLBACK_URLS` setzt Fallbacks als CSV-Liste.

## Dashboard API
- `GET /api/v1/dashboard/overview`
  - liefert Event-Historie, Jahresverteilung (`activity_years`), Asset-Bestände und automatische Rollenerkennung (private/business).
  - enthält `summary.suggested_tax_year` basierend auf importierten Event-Jahren.
- `POST /api/v1/dashboard/role-override`
  - speichert UI-Override für Steuerrolle (`auto|private|business`).

## Wallet Groups (Virtuelle Wallet)
- `GET /api/v1/wallet-groups`
- `POST /api/v1/wallet-groups/upsert`
- `POST /api/v1/wallet-groups/delete`
- Zweck:
  - mehrere Wallet-Adressen als eine logische Portfolio-Einheit verwalten
  - gruppierte Live-Balance und gruppierter Solana-Import

## Processing UX-Hinweis
- `POST /api/v1/process/run` liefert Warnung `tax_year_no_events`, wenn für das gewählte Jahr keine Events gefunden werden.

## Audit API
- `GET /api/v1/audit/tax-line/{job_id}/{line_no}`
  - liefert Drilldown für eine Tax-Line inklusive:
    - gespeicherter Tax-Line-Daten
    - verknüpftem `raw_event` über `source_event_id`
    - kompakter Berechnungs-Trace (`gain_loss_eur = proceeds_eur - cost_basis_eur`)

## Compliance & Qualität
- KI-4-Augen-Prinzip (entkoppelte Prompt-Generierung für Logik und Tests).
- Pflicht-Regression über Golden Cases (`DE-2024`, `DE-2025`, `DE-2026`).
- Branch Protection + Required Checks + signierte Commits.

## Security Konfiguration
- Secrets werden serverseitig verschlüsselt (AES-256-GCM) gespeichert.
- Optionaler Master-Key via Umgebungsvariable:
  - `STEUERREPORT_MASTER_KEY_B64` (Base64-codierter 32-Byte-Key)
- Ohne gesetzte Variable wird beim ersten Secret-Write ein lokaler Key unter
  `/tmp/steuerreport/master.key` erzeugt.

## Dokumentation
Zentraler Dossier-Index:
- [docs/README_DOSSIER_INDEX.md](docs/README_DOSSIER_INDEX.md)

Wichtige Kern-Dokumente:
- [docs/13_MODULARE_STEUER_ENGINE.md](docs/13_MODULARE_STEUER_ENGINE.md)
- [docs/14_INTEGRITAET_VERSIONIERUNGS_KEYS.md](docs/14_INTEGRITAET_VERSIONIERUNGS_KEYS.md)
- [docs/15_GITHUB_WORKFLOW_COMPLIANCE.md](docs/15_GITHUB_WORKFLOW_COMPLIANCE.md)
- [docs/16_SOLANA_RPC_PROVIDER_STRATEGIE.md](docs/16_SOLANA_RPC_PROVIDER_STRATEGIE.md)
- [docs/18_ROADMAP_EXECUTION_PLAN.md](docs/18_ROADMAP_EXECUTION_PLAN.md)
- [docs/19_BMF_2025_STEUERREGELN_UND_PFLICHTEN.md](docs/19_BMF_2025_STEUERREGELN_UND_PFLICHTEN.md)
