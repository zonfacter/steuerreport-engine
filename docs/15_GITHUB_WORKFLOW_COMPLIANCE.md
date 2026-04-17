# GitHub Workflow Compliance (Solo + KI)

## 1. Ziel
Ersatz des klassischen 4-Augen-Prinzips durch ein synthetisches Prüfmodell aus:
- verpflichtender Testtrennung,
- harter CI-Pipeline,
- Branch-Protection und Commit-Integrität.

## 2. KI-4-Augen-Prinzip
- Logik und Tests werden getrennt erzeugt (separate Prompts/Kontexte).
- Kritische Logik darf nur gemerged werden, wenn:
  - Unit-/Integrationstests grün sind,
  - Golden Cases unverändert sind,
  - PR-Checkliste vollständig ist.

## 3. Pflicht-Checks (Required Checks)
- `dependency-audit`
- `static-analysis` (`ruff`, `mypy`)
- `tests-and-coverage`
- `golden-hash-verification`

## 4. Coverage-Policy
- Kritische Core-Pfade (`fifo`, `ruleset`, `fx_engine`, `integrity_manager`): `>= 95%`.
- API-Handler: `>= 80%`.
- UI-Komponenten: `>= 70%`.

## 5. Branch-Protection
- Kein Direkt-Push auf `main`.
- Merge nur via Pull Request.
- `Require status checks to pass` aktiviert.
- `Require branches to be up to date before merging` aktiviert.
- `Dismiss stale approvals when new commits are pushed` aktiviert.
- `Require signed commits` aktiviert.

## 6. Supply-Chain-Sicherheit
- GitHub Actions werden über Commit-SHA gepinnt.
- Kein unpinned `uses:` in produktiven Workflows.

## 7. Golden Hash Integrity
- Golden-Case-Hashvergleich ist blockierend.
- Vergleich nur über fachliche Ergebnisfelder.
- Änderungen an Ruleset/Config müssen neue Referenzversionen dokumentieren.

## 8. PR-Governance
- PR-Template ist verpflichtend.
- Für kritische Module muss die KI-Compliance-Checkliste vollständig sein.
- Bei roten Integritätschecks: Merge strikt verboten.
