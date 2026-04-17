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

## Developer Commands
- `make lint` Ruff-Checks
- `make typecheck` Mypy-Prüfung
- `make test-cov` Testlauf mit Coverage
- `make ci` lokaler CI-ähnlicher Sammellauf

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
