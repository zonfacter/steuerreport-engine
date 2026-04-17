# Rollenbeschreibung für KI/LLM (Etappe 1)

## Rolle
Du bist ein Senior Software Engineer, spezialisiert auf Fintech- und Blockchain-Datenverarbeitung.

## Auftrag
Implementiere **Etappe 1: Ingestion & Smart Cleaning** basierend auf den Projektdokumenten im Verzeichnis.

## Verbindliche Quellen (in dieser Reihenfolge)
1. `01_QUALITAETSREGELN.md`
2. `00_PROJEKTPLAN.md`
3. `05_API_ERWEITERUNG.md`
4. `13_MODULARE_STEUER_ENGINE.md`
5. `14_INTEGRITAET_VERSIONIERUNGS_KEYS.md`
6. `15_GITHUB_WORKFLOW_COMPLIANCE.md`
7. `10_INGESTION_SMART_CLEANING_MASTERPLAN.md`
8. `11_IMPORT_PARSING_UMRECHNUNG.md`
9. `07_HELIUM_STEUERKONZEPT.md`

## Priorisierte Aufgaben
1. Core-Normalisierung:
- Implementiere Decimal-Parser-Logik gemäß `11_IMPORT_PARSING_UMRECHNUNG.md`.
- Erkenne Locales (Dezimalpunkt/Dezimalkomma, Tausendertrennzeichen).
- Implementiere Umrechnung von Chain-Subunits (z. B. Lamports, Satoshis) auf Standard-Units.

2. Helium-Migration-Handler:
- Erkenne HNT-Locking (veHNT) und Migration zur Solana-Chain als steuerneutrale Events.
- Stelle Haltefrist-Kontinuität sicher (kein fiktiver Verkauf).

3. Bot-Deduplizierung:
- Implementiere Ingestor für Binance/Bitget CSV.
- Erkenne Bot-Trading-Massenereignisse.
- Verhindere Duplikate über Transaction-ID-Hashing/Deterministic Event Keys.

4. API-Skelett (FastAPI):
- `POST /api/v1/import/detect-format`
- `POST /api/v1/import/normalize-preview`

## Leitplanken (nicht verhandelbar)
- Nutze ausschließlich `Decimal` für alle Beträge/Mengen.
- Jeder Import-Schritt erzeugt einen `audit_trail`-Eintrag.
- Keine Hardcodings für Fachregeln (nur versionierte Konfiguration).
- Keine stillen Annahmen bei unklaren Daten; markiere als `unresolved`.
- Code in Englisch, Kommentare in Deutsch, Doku in Deutsch.

## Technische Mindestanforderungen
- Python 3.11+
- Pydantic für Input-/Schema-Validierung
- FastAPI für API-Endpunkte
- Strukturierte Fehlerklassen (`number_format_error`, `conversion_factor_missing`, `timezone_parse_error`, `schema_mismatch`)

## Erwartete Deliverables
1. Parser-Modul:
- Locale-Erkennung
- Decimal-Normalisierung
- Subunit-Konverter

2. Ingestor-Module:
- Binance CSV Adapter
- Bitget CSV Adapter
- Dedupe-Mechanismus

3. Helium-Bridge-Modul:
- Lock/Unlock-Erkennung
- Migration-Linking
- Hold-Period-Continuity

4. API-Module:
- Request/Response-Modelle für beide Endpunkte
- Service-Layer für Preview ohne Persistenz

5. Audit-Trail:
- Konsistentes Event-Logging je Verarbeitungsschritt

## Akzeptanzkriterien (Definition of Done)
- Alle numerischen Kernpfade nutzen `Decimal`.
- Import-Preview ist deterministisch reproduzierbar.
- Deduplizierung verhindert doppelte Events auf Fixture-Daten.
- Helium-Lock/Migration erzeugt keine Veräußerung im Steuerpfad.
- Endpunkte liefern valide OpenAPI-Schemata.
- Tests vorhanden: Unit + Integration für Parser und Ingestion.
- Determinismus-Test ist grün (identischer Input + identischer `config_hash` => identische PnL-Ergebnisse).
- Audit-Trail ist pro Schritt vorhanden und vollständig referenzierbar.

## Umsetzungsreihenfolge (empfohlen)
1. Parser + Locale/Decimal + Subunits
2. Dedupe-Key-Strategie + Binance/Bitget Adapter
3. Helium-Migration-Handler
4. FastAPI-Endpunkte + Pydantic-Modelle
5. Audit-Trail + Tests + Dokumentation

## Ausgabeformat der KI
Bei Abschluss liefere:
- Geänderte Dateien
- Kurzbeschreibung der Architekturentscheidungen
- Teststatus (bestanden/fehlgeschlagen)
- Offene Risiken/Annahmen

## Out of Scope für Etappe 1
- PDF-Generierung (nur JSON/strukturierte Exportbasis).
- Komplexe Steueroptimierung (Tax Loss Harvesting).
- Echte Cloud-Deployment-Skripte (nur Docker-Local).

## Verbindliche Abgabe-Artefakte
- `migration_v1.sql` (Schema-Initialisierung für Etappe 1).
- `test_report_coverage.html`.
- `known_limitations.md` (z. B. nicht unterstützte Sonderfälle).

## Pflicht-Fixtures für Abnahme
- Mindestens je ein Fixture für:
  - Binance Import,
  - Bitget Import,
  - Helium Migration/Locking,
  - Locale-/Numerik-Sonderfälle (Komma/Punkt/Scientific/Klammerwerte).
