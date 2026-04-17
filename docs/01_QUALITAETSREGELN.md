# Qualitätsregeln und Verifikation

## 1. Sprach- und Dokumentationsregeln
- Code (Identifier, Funktionsnamen, Klassen, Dateinamen): Englisch.
- Kommentare im Code: Deutsch.
- Technische Dokumentation: Deutsch.

## 2. Keine Halluzinationen
- Unklare oder unvollständige Daten niemals erraten.
- Stattdessen: Fall als `unresolved` markieren und in Review-Liste aufnehmen.
- Jede automatische Entscheidung muss begründet und im Audit-Trail nachvollziehbar sein.

## 3. Keine Hardcodings
- Keine festen Schwellenwerte, Regeln oder Mappings im Kerncode.
- Alles fachlich Relevante kommt aus versionierten Konfigurationsdateien.
- Änderungen erfolgen über Regelversionen, nicht über versteckte Code-Patches.

## 4. Verbindliche technische Standards
- Zahlenlogik nur mit `Decimal`.
- Typisierung mit `mypy` (strikt in Kernmodulen).
- Laufzeitvalidierung von Eingaben mit Pydantic.
- Strukturierte Logs mit Run-ID.

## 5. Teststrategie (Pflicht)
- Unit-Tests: FIFO, Derivate, Klassifizierung.
- Integrationstests: Ingestion -> Normalisierung -> Engine -> Reporting.
- Regressionstests: jeder behobene Fehlerfall als Fixture.
- Property-Tests: Invarianten (z. B. Inventar-Konsistenz).
- Lasttests: 30k+ Datensätze.
- Mindest-Coverage:
  - Kritische Core-Pfade (FIFO/PnL/FX/Derivate): `>= 95%`.
  - API-Handler: `>= 80%`.
  - UI-Komponenten: `>= 70%`.

## 6. CI/CD Quality Gates
- `ruff format`
- `ruff check`
- `mypy`
- `pytest` inkl. Coverage-Grenzen
- Dependency-Sicherheitscheck (z. B. `pip-audit`)

Merge ist nur erlaubt, wenn alle Gates grün sind.

## 7. Auditierbarkeit und Reproduzierbarkeit
- Jeder Steuerwert muss rückverfolgbar sein: Quelle, Regelversion, Timestamp, FX-/Preisquelle.
- Gleicher Input + gleiche Konfiguration => gleicher Output.
- Exportartefakte tragen Versionsinformationen der Regeln/Schemata.
- Determinismusregel:
  - Bei identischem `config_hash` und identischen Inputs müssen PnL-Ergebnisse bit-identisch sein.
  - Variabel sein dürfen ausschließlich `run_id`, `execution_time`, `trace_id`.

## 7.1 Security- und Secret-Regeln
- Secrets (API-Keys/Tokens) werden verschlüsselt gespeichert (`AES-256-GCM`).
- Schlüsselverwaltung:
  - Der Master-Key liegt nicht in der SQLite-Datenbank.
  - Key-Rotation und `key_version` müssen unterstützt werden.
- Logging-Regeln:
  - Keine Klartext-Secrets, Passwörter oder vollständige Wallet-Adressen.
  - Wallet-Adressen werden maskiert (z. B. `0x12...abcd`).

## 8. Definition of Done pro Feature
- Fachlich korrekt gemäß Spezifikation.
- Tests vorhanden und grün.
- Logging/Audit-Trail ergänzt.
- Dokumentation aktualisiert (Deutsch).
- Keine offenen kritischen Warnungen ohne explizite Freigabe.

## 9. KI-Compliance (Vibe Coding / Copilot)
### 9.1 Entkoppeltes KI-4-Augen-Prinzip
- Separations-Regel: Logik-Code und zugehörige Unit-Tests dürfen nicht im selben KI-Prompt erzeugt werden.
- Schrittfolge:
  - Schritt 1: Logik implementieren.
  - Schritt 2: In neuem Kontext Testanforderungen formulieren und Tests erzeugen.

### 9.2 Pflicht-Checkliste für kritische Module
Gilt für: `fifo`, `ruleset`, `fx_engine`, `integrity_manager`.
- `[ ]` Logik manuell zeilenweise auditiert (kein Blackbox-Code).
- `[ ]` Randfälle (z. B. Liquidation, 0-Bestand, Precision-Loss) durch Tests abgedeckt.
- `[ ]` Golden-Case-Vergleichslauf für betroffene Steuerjahre erfolgreich.

### 9.3 Golden Cases und Regression
- Pro unterstütztem Steuerjahr (mindestens `DE-2024`, `DE-2025`, `DE-2026`) existiert mindestens ein Golden Case.
- Golden Cases enthalten Referenz-Transaktionen + erwartetes Ergebnisartefakt.
- Hashvergleich erfolgt ausschließlich auf fachlichen Ergebnisfeldern (ohne `run_id`, `trace_id`, `execution_time`).

### 9.4 Branch- und Commit-Integrität
- Kein Direkt-Push auf `main`; Änderungen laufen über Pull Request.
- Merge nur bei grünen Required Checks.
- Signierte Commits (GPG/SSH) sind verpflichtend für produktive Branches.
