# Projektplan: Cross-Chain-Steuerreport (Deutschland, ab Steuerjahr 2020)

Verbindlicher Zusatzleitfaden für UX/Import/Processing: `17_UX_IMPORT_PROCESSING_MASTERPLAN.md`.
Verbindlicher Fachleitfaden für BMF 2025: `19_BMF_2025_STEUERREGELN_UND_PFLICHTEN.md`.

## 1. Zielbild und Leitplanken
- Rechtsraum: Deutschland (`DE`), Steuerjahre ab `2020`.
- Lastziel: Verarbeitung von `30.000+` Transaktionen je Lauf.
- Quellen: Binance, Bitget, Coinbase, Phantom/Solana, Helium Legacy.
- Rechenpräzision: ausschließlich `Decimal`.
- Report-Export: PDF-Splitting auf maximal `100 Seiten` je Datei.
- Keine Hardcodings in Kernlogik: Regeln, Schwellen und Mappings konfigurationsgetrieben und versioniert.
- §23-Freigrenze und §22-Freigrenze sind technisch getrennte Ruleset-Parameter.

## 2. Etappenplan mit Abnahmekriterien

### Etappe 0: Projektbasis und Quality-Gates
Lieferobjekte:
- Struktur (`src/`, `tests/`, `configs/`, `docs/`, `scripts/`).
- Reproduzierbare Umgebung (Lockfile, Task Runner).
- CI-Grundpipeline (Format, Lint, Typprüfung, Tests).
- Konfigurationssystem (Datei + Env Overrides).
- Ruleset-Registry-Grundstruktur (Core vs. Ruleset Provider).

Abnahme:
- Frischer Checkout läuft ohne manuelle Nacharbeit.
- Basis-Gates sind grün.

### Etappe 1: Ingestion + Schema-Versionierung (erweitert)
Lieferobjekte:
- Adapter pro Quelle für CSV/JSON.
- Versioniertes, einheitliches Ereignisschema.
- Pydantic-Modelle für strikte Laufzeitvalidierung.
- Klare Fehlerausgabe bei Schema-Drift (z. B. umbenannte Spalten in Bitget-Exporten).
- Event-Fingerprinting (`unique_event_id`) beim Persistieren.

Abnahme:
- Referenzdateien je Quelle werden vollständig normalisiert.
- Unbekannte oder fehlerhafte Felder werden explizit gemeldet, nicht verworfen.

### Etappe 2: Reconciliation / Transfer-Matching (erweitert)
Lieferobjekte:
- Erkennung interner Transfers wallet-/exchange-übergreifend.
- Time-Window-Matching für zeitversetzte Ein-/Ausgänge.
- Mengenabgleich mit Toleranz (Netzwerk-Fee berücksichtigen).
- Konfidenz-Score (`high`, `medium`, `low`) mit Review-Queue.

Abnahme:
- Kein falsches Realisieren von Gewinnen bei gematchten Eigenüberträgen.
- Deterministisches Matching bei identischer Konfiguration.

### Etappe 3: Spot-Engine (FIFO)
Lieferobjekte:
- Deque-basierte FIFO-Lot-Verarbeitung.
- Gebührenkorrekte Kosten-/Erlöslogik.
- Haltedauerberechnung und Trennung >365 Tage vs. steuerpflichtig.
- Short-Sell-Guard mit klarer Fehlerdiagnostik.

Abnahme:
- Tests für Teilverkäufe, Multi-Lots, Fee-Assets, Unterdeckung.
- Inventargleichung je Asset erfüllt.

### Etappe 4: Derivate-Engine (erweitert)
Lieferobjekte:
- `DerivativesManager` für `Margin_Open` -> `Margin_Close|Liquidation`.
- EUR-PnL inkl. Gebühren/Funding.
- Liquidationslogik inkl. Negative-Equity-Fall:
  - Collateral kann auf null fallen.
  - Zusätzliche Gebühren/Funding als realisierter Verlust buchen.
  - Zuordnung in den korrekten Topf: Termingeschäfte.

Abnahme:
- Testfälle für Gewinn, Verlust, Teil-Schließung, Liquidation, Negative Equity.
- Keine Vermischung mit Spot-Inventar.

### Etappe 5: DeFi-Logik (Solana/Jupiter/Helium)
Lieferobjekte:
- Sliding-Window-Grouping für Sub-Events (Signer + Block/Zeitfenster).
- Multi-Hop-Aggregation auf ökonomisches Netto rein/raus.
- Helium Legacy -> Solana regelbasierte Migrationszuordnung.
- Claim-Events als Zufluss zum Marktwert am Claim-Zeitpunkt.

Abnahme:
- Multi-Hop-Fälle korrekt zu einem ökonomischen Swap verdichtet.
- Migration/Claim korrekt klassifiziert und auditierbar.

### Etappe 6: Bewertungs- und FX-Schicht
Lieferobjekte:
- Historische FX-/Preisumrechnung mit Quellennachweis.
- Fallback-Reihenfolge und Caching.
- Harte Behandlung fehlender Marktdaten (Flag statt Schätzung).
- Berechnungspfad immer mit explizitem `ruleset_id` und `ruleset_version`.
- Bewertungsmethode (`sekundengenau`, Tageskurs, Tagesendkurs) je Veranlagungszeitraum konsistent dokumentieren.

Abnahme:
- Jeder EUR-Wert ist rückverfolgbar.
- Fehlende Daten erzeugen Review-Items.
- Kursquelle, Kursdatum und FX-Quelle sind im Audit exportierbar.

### Etappe 7: Reporting + PDF-Export
Lieferobjekte:
- CSV/JSON mit Pflichtfeldern:
  - `Datum_Kauf`, `Datum_Verkauf`, `Asset`, `Menge`, `Anschaffungskosten_EUR`, `Veraeusserungserloes_EUR`, `Gewinn_Verlust_EUR`, `Typ`, `Haltedauer_Tage`
- PDF-Export mit automatischem Splitting auf max. `100 Seiten` je Datei.
- Audit-Anhang (Regelversion, Konfig-Hash, Warnungen, offene Fälle).
- Report-Integritäts-ID (`report_integrity_id`) und optional QR pro PDF-Seite.

Abnahme:
- Splitting für >100 Seiten getestet.
- Exporte sind schema-versioniert und reproduzierbar.

### Etappe 8: Verifikation, Performance, Übergabe
Lieferobjekte:
- End-to-End-Tests mit 30k+ Datensätzen.
- Performance-/Speicherprofile.
- Differenztests gegen Referenzrechnungen.
- Übergabepaket für Steuerberater.
- Snapshot-Artefakte je finalisiertem Run.

Abnahme:
- Alle Gates erfüllt, Restunsicherheiten dokumentiert.

## 3. Architektur-Leitplanken (verbindlich)
| Komponente | Architekturentscheidung | Grund |
|---|---|---|
| Rechenkern | `from decimal import Decimal` | Vermeidung von Rundungsfehlern |
| Datenhaltung | Polars oder Pandas (Ingestion), Deque (FIFO) | Performance + FIFO-Effizienz |
| PDF-Engine | WeasyPrint oder ReportLab | Präzise Seitenumbrüche und Splitting |
| DeFi-Aggregation | Sliding-Window-Grouping | Robuste Bündelung von Sub-Events |

## 4. Sprint-1 Reihenfolge (empfohlen)
1. Grundgerüst + Quality Tooling.
2. Einheitliches Ereignisschema + 2 Adapter als Vorlage.
3. FIFO-Kern mit Invariantentests.
4. `DerivativesManager` inkl. Liquidation/Negative-Equity-Tests.
5. Erstes CSV/JSON-Reporting mit Snapshot-Tests.
6. PDF-Prototyp mit 100-Seiten-Limit und Splitting-Tests.

## 5.1 Ergänzung: Trade Republic und Bucket-Trennung
- Spezifisches Importprofil für Trade Republic (v1, versionierbar).
- Steuerliche Bucket-Trennung (`KAP`, `SO`, `DERIV`) als Pflichtklassifikation.
- Konfigurierbarer FIFO-Modus: global oder depot-/wallet-spezifisch (`fifo_mode`).
- Cross-Plattform-Schwellen-Tracker als eigener Verarbeitungsschritt.

## 5.2 Ergänzung: Smart Cleaning und Klassifikation
- Universal Reward & Staking Engine als Ingestion-Teilmodul.
- Helium-Migration-Bridge (Lock/Unlock ohne fiktive Veräußerung).
- Plausibilitäts-Tresor für Differenzbuchungen mit Freigabepflicht.
- Gewerbe-Ampel als Hinweislogik mit Review-Pflicht.
