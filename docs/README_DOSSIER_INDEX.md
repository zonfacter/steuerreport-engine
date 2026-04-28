# Steuerreport-Projekt (DE, ab 2020)

## Zweck
Dieses Verzeichnis enthält die verbindliche Fach-, Architektur- und Qualitätsdokumentation für die Cross-Chain-Steuerengine.

## Dokumentenindex
- `00_PROJEKTPLAN.md`: Etappen, Meilensteine, Abnahmekriterien.
- `01_QUALITAETSREGELN.md`: Coding-, Test- und Verifikationsregeln.
- `02_ARCHITEKTUR_VORSCHLAG.md`: Zielarchitektur (Frontend/Backend/DB/Deployment).
- `04_UI_ANFORDERUNGEN.md`: Review-First Oberfläche und UX-Pflichten.
- `05_API_ERWEITERUNG.md`: API-Endpunkte für Import, Review, Audit, Export.
- `06_WETTBEWERBS_FEATURES.md`: Komfort-/Strategie-Features für Wettbewerbsfähigkeit.
- `07_HELIUM_STEUERKONZEPT.md`: Helium-spezifische Fachlogik, Bewertung, Mapping, Audit.
- `08_STEUERLOGIK_TRADEREPUBLIC_2026.md`: Steuerliche Bucket-Logik, Trade-Republic-Integration, Compliance-Checks.
- `09_DEPOT_TRENNUNG_KONZEPT.md`: Depot-Separation, Transfer-Bridge, Hard-Silo-Regeln, Silo-Dashboard.
- `10_INGESTION_SMART_CLEANING_MASTERPLAN.md`: Universal Reward Engine, Helium-Bridge, Adjustments, Gewerbe-Ampel.
- `11_IMPORT_PARSING_UMRECHNUNG.md`: Import-Locale, Dezimaltrennung, Umrechnungsfaktoren, Parser-Validierung.
- `12_LLM_ROLLENBESCHREIBUNG_ETAPPE1.md`: Ausführungsrolle/Prompt für die Implementierungs-KI in Etappe 1.
- `13_MODULARE_STEUER_ENGINE.md`: Pluggable Ruleset-Architektur, Versionierung, RuleContext.
- `14_INTEGRITAET_VERSIONIERUNGS_KEYS.md`: Chain-of-Trust, Fingerprints, Snapshot-Strategie.
- `15_GITHUB_WORKFLOW_COMPLIANCE.md`: KI-4-Augen-Prinzip, CI-Gates, Branch-Protection, PR-Governance.
- `16_SOLANA_RPC_PROVIDER_STRATEGIE.md`: RPC-Provider-Reihenfolge, Free-Tier-Betrieb, Retry-/Fallback-Regeln.
- `17_UX_IMPORT_PROCESSING_MASTERPLAN.md`: Integrations-Hub, vereinfachter Nutzerfluss, Wizard-basiertes Steuer-Processing, Import-Feedback, Portfolio-Sets, Exportstrategie.
- `18_ROADMAP_EXECUTION_PLAN.md`: Umsetzungsplan mit Sprints, Sequenzierung, Akzeptanzkriterien und Risiken.
- `19_BMF_2025_STEUERREGELN_UND_PFLICHTEN.md`: Technische Umsetzung des BMF-Schreibens vom 06.03.2025, inkl. Ruleset-Freigrenzen, Wallet-FIFO, Bewertung, Dokumentationspflichten.

## Single Source of Truth (SSoT)
Bei Überschneidungen gilt folgende Priorität (höchste Priorität zuerst):
1. `01_QUALITAETSREGELN.md`
2. `00_PROJEKTPLAN.md`
3. `05_API_ERWEITERUNG.md`
4. `04_UI_ANFORDERUNGEN.md`
5. `13_MODULARE_STEUER_ENGINE.md`
6. `19_BMF_2025_STEUERREGELN_UND_PFLICHTEN.md`
7. `14_INTEGRITAET_VERSIONIERUNGS_KEYS.md`
8. `15_GITHUB_WORKFLOW_COMPLIANCE.md`
9. `10_INGESTION_SMART_CLEANING_MASTERPLAN.md`
10. `11_IMPORT_PARSING_UMRECHNUNG.md`
11. `12_LLM_ROLLENBESCHREIBUNG_ETAPPE1.md`
12. `07_HELIUM_STEUERKONZEPT.md`
13. `08_STEUERLOGIK_TRADEREPUBLIC_2026.md`
14. `09_DEPOT_TRENNUNG_KONZEPT.md`
15. `02_ARCHITEKTUR_VORSCHLAG.md`
16. `06_WETTBEWERBS_FEATURES.md`
17. `16_SOLANA_RPC_PROVIDER_STRATEGIE.md`
18. `17_UX_IMPORT_PROCESSING_MASTERPLAN.md`
19. `18_ROADMAP_EXECUTION_PLAN.md`

## Verbindliche Leitplanken
- Code in Englisch, Kommentare und Dokumentation in Deutsch.
- Keine Halluzinationen: unklare Fälle als `unresolved` kennzeichnen.
- Keine Hardcodings in Fachlogik.
- Rechenkern mit `Decimal`.
- PDF-Export mit maximal `100 Seiten` je Datei.
- Jede Berechnung auditierbar (`run_id`, `config_hash`, `ruleset_version`).

## Arbeitsprinzip
- Erst deterministisch verarbeiten, dann optimieren.
- Erst Auditierbarkeit sicherstellen, dann Komfortfunktionen ausbauen.
- Jede Automatikentscheidung muss für Nutzer und Steuerberater erklärbar sein.
