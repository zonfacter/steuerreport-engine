# 17_UX_IMPORT_PROCESSING_MASTERPLAN

## Zielbild (Produktperspektive)
Die Anwendung wird vom technischen Workflow (Import -> Reconcile -> Process -> Review) zu einem nutzergeführten Integrations-Workflow umgebaut:
1. Integrationen verbinden
2. Historie vollständig laden
3. Virtuelle Portfolios bilden
4. Steuerberechnung über Wizard starten
5. Finanzamt-/Steuerberater-Export erzeugen

Wichtig: Keine freie Texteingabe für steuerlich kritische Processing-Parameter.

## Benchmark-orientierte Leitlinien (Blockpit/Koinly/CoinTracking)
Aus öffentlich verfügbaren Produkt-/Help-Dokumentationen abgeleitete UX-Prinzipien:
- Wallet/Exchange-first statt Technik-first.
- API + CSV parallel als gleichwertige Importpfade.
- Sichtbares "Review needed" bei Datenlücken.
- Vollständigkeits- und Dublettenhinweise pro Integration.
- Mehrfach-Wallet-Import und Gruppierung zu einem Gesamtportfolio.

Referenzen (Stand 2026-04-19):
- Koinly Getting Started: https://support.koinly.io/en/articles/9489951-getting-started-with-koinly
- Koinly CSV/Excel Import: https://support.koinly.io/en/articles/9489978-how-to-import-a-csv-or-excel-file
- Koinly API Limitations: https://support.koinly.io/en/articles/9490003-api-sync-exchange-api-limitations
- CoinTracking Wallet Import: https://cointracking.info/import/wallet_tx/
- Blockpit Solana DeFi Import: https://help.blockpit.io/hc/en-us/articles/7083023446044-DeFi-import-solution-for-Solana-SOL-based-applications-dApps

## Produkt-Informationsarchitektur (neu)
### Hauptnavigation
- Integrationen
- Portfolio
- Steuerlauf
- Review
- Exporte
- Admin

### Integrationen (Primary Entry)
Jede Integration hat denselben Bedienvertrag:
- Verbinden
- Vollimport starten
- Delta-Sync starten
- Status/Health
- Letzter Import (Zeit, Rows, Duplicates, Warnings)

Unterstützte Typen:
- Solana/Phantom (einzeln + Bulk Wallet)
- Binance (API + CSV/XLS)
- Bitget
- Coinbase
- Helium Legacy (Datei-/Offline-Import)

## Import- und Sync-Design
### Import-Jobmodell (verbindlich)
Jeder Import erzeugt einen Job mit:
- `job_id`, `integration_id`, `scope`, `started_at_utc`, `finished_at_utc`
- `status`: queued|running|success|partial|error
- `fetched_rows`, `inserted_events`, `duplicate_events`, `warning_count`, `error_count`
- `details_json`

### Import-Aktivitätsprotokoll (UI)
- Persistentes Protokoll (nicht nur Toast).
- Live-Status während Laufzeit.
- Direktaktion: "Details", "Wiederholen", "Abbrechen" (wenn möglich).
- Filter nach Integration und Status.
- Umsetzung im Import-Hub: Connector-/Statusfilter, Detailauswahl, Source-ID-Kopie und Wiederholsprung zur passenden Import-Konfiguration.

### Vollständigkeit und Qualität
- Quellenspezifische Limit-Hinweise (API-Limits, bekannte Lücken).
- Automatische Empfehlung bei unvollständigen API-Daten: CSV ergänzen.
- Dubletten-Schutz mit Fingerprints (API + CSV Koexistenz).

## Virtuelle Wallet / Portfolio-Sets
### Konzept
Ein Portfolio-Set bündelt mehrere Integrationen/Wallets logisch zu einem Gesamtportfolio.

### Funktionen
- Set erstellen/bearbeiten/löschen.
- Integrationen zuordnen.
- Quellenfilter pro Set speichern, damit Solana RPC, Binance API, Blockpit-Referenzimporte und Helium Legacy getrennt oder gemeinsam betrachtet werden können.
- Überblick je Set:
  - Gesamtwert EUR/USD
  - Asset-Allokation
  - Verlauf
  - Quellenbeitrag pro Integration
- Set-spezifischer Wertverlauf basiert auf den zugeordneten Quellen und wird getrennt von globaler Portfolio-Wertentwicklung dargestellt.

### Steuerlicher Zweck
- Trennung nach Depot-Logik weiterhin möglich.
- Zusätzlich konsolidierte Sicht für Nutzer und Steuerberater.

## Steuerlauf (Wizard statt Freitext)
### Wizard-Schritte
1. Steuerjahr wählen (`tax_year` Dropdown)
2. Regelwerk wählen (`ruleset_id` Dropdown + Beschreibung)
3. Depotmodus wählen (global/depot_separated)
4. Datenumfang wählen (Portfolio-Set / Integrationen)
5. Validierungen aktivieren (Short-Sell Guard, Transfercheck, Haltefrist)
6. Dry-Run oder Final-Run starten

### Pflichteigenschaften
- Keine freien Textfelder für `ruleset_id`, `tax_year`, kritische Flags.
- Nur validierte Optionen aus `/api/v1/process/options`.
- Vor Start zwingender Preflight.
- Die UI darf `POST /api/v1/process/run` erst auslösen, wenn `POST /api/v1/process/preflight` keine Blocker liefert.
- Preflight-Ergebnis wird sichtbar im Steuerlauf angezeigt, inklusive Anzahl Events im Steuerjahr, offene Transfers, High-Issues und Bewertungswarnungen.
- Jede Preflight-Meldung kann eine Guided Action enthalten, damit Nutzer nicht raten müssen, ob sie Import, Transfer-Review oder Issue-Inbox öffnen müssen.

## Preflight-Check (vor jedem Run)
### Blocker
- Keine Importdaten vorhanden.
- Offene High-Severity-Issues.
- Unmatched Transfers über Schwellwert.
- Fehlendes Ruleset für Zeitraum.

### Warnungen
- Preis-/FX-Abdeckung unvollständig.
- Integrationen mit bekannten API-Lücken.
- Hoher Anteil unklassifizierter Events.

## Review-Workflow
- Automatische "Review needed"-Inbox aus Blockern/Warnungen.
- Guided Actions je Issue-Typ (statt Rohdatenzwang) mit vorbelegten UI-Filtern.
- Gate-Status für Exportfreigabe (`allow_export`).

## Import/Export für Steuerlauf-Konfiguration
### Konfigurationsprofile
- Speichern/Laden als JSON.
- Versioniert und hashbar.
- Standardprofile:
  - DE Privat Standard
  - DE Trading + Derivate
  - DE Mining/Staking

### Steuerpaket-Export
Enthält:
- Reports (CSV/JSON/PDF)
- Run-Metadaten (`run_id`, `ruleset_id`, `ruleset_version`, `config_hash`)
- Audit-Trace
- Integritäts-ID

## PDF-Export-Regel
- Maximal 100 Seiten pro Datei.
- Automatisches Splitting (`part_01`, `part_02`, ...).
- Jede Seite mit Integritätskennung.

## API-Zielbild (zusätzlich zu bestehenden Endpunkten)
- `GET /api/v1/integrations`
- `POST /api/v1/integrations/{id}/sync-full`
- `POST /api/v1/integrations/{id}/sync-delta`
- `GET /api/v1/integrations/jobs`
- `GET /api/v1/portfolio/integrations`
- `POST /api/v1/portfolio/sets`
- `GET /api/v1/portfolio/sets/{id}/overview`
- `GET /api/v1/process/options`
- `POST /api/v1/process/preflight`
- `POST /api/v1/process/profile/save`
- `POST /api/v1/process/profile/load`
- `POST /api/v1/process/export`

## Etappenplan (verbindlich)
### Etappe A: UX- und Import-Basis
- Integrations-Hub als primärer Einstieg.
- Import-Aktivitätsprotokoll mit Jobstatus.
- Bulk-Solana-Wallet-Import.
- Erste Integrationsübersicht pro Quelle.

Abnahme:
- Nutzer kann ohne Doku 3 Integrationen hinzufügen und Vollimporte starten.
- Jeder Import liefert sichtbares, persistentes Feedback.

### Etappe B: Virtuelle Wallet und Portfolio-Sets
- Sets erstellen und Integrationen zuordnen.
- Gesamtportfolio-Ansicht mit Verlauf und Quellanteilen.

Abnahme:
- Ein Set über mindestens 2 Integrationen zeigt konsolidierte Werte.

### Etappe C: Steuerlauf-Wizard + Preflight
- Wizard ohne Freitext für Steuerparameter.
- Preflight-Blocker/Warnungen.
- Profile speichern/laden.

Abnahme:
- Steuerlauf kann ausschließlich über Wizard abgeschlossen werden.

### Etappe D: Export- und Audit-Paket
- Steuerpaket-Export inkl. Splitting-Logik für PDF.
- Integritäts-ID in allen Exporten.

Abnahme:
- Export erfüllt 100-Seiten-Regel automatisiert.

### Etappe E: Helium Legacy Vertiefung
- Legacy-Importpfad und Migrations-/Staking-spezifische Klassifizierung.
- CoinTracking-/Fairspot-kompatiblen Legacy-HNT-Export erkennen und ohne Duplikate importieren.
- Transfergegenparteien tabellarisch sichtbar machen, damit ausgehende Staking-Transfers und spätere Rückflüsse überprüfbar sind.
- Review-Fälle für unklare Legacy-Zuordnung.

Abnahme:
- Legacy-Daten sind im Portfolio-Set und Steuerlauf nutzbar.
- Gegenwallets, gesendete/erhaltene HNT, Gebühren und Beispiel-Transaktionen sind im Transfer-Review sichtbar.

## Qualitäts- und Rechtsleitplanken
- `Decimal`-Pflicht im Rechenkern.
- Deterministische Re-Runs bei gleichem Config/Ruleset.
- Vollständiger Audit-Trail je Nutzeraktion.
- Keine Hardcodings in steuerlicher Fachlogik.
- Fachliche Umsetzung nach deutschem Steuerkontext; finale steuerrechtliche Würdigung erfolgt durch Steuerberater.

## Priorität in der Umsetzung
1. Nutzerführende Bedienbarkeit
2. Vollständige und nachvollziehbare Imports
3. Reproduzierbarer Steuerlauf
4. Export- und Audit-Sicherheit
