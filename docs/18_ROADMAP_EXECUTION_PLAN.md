# Roadmap-Ausführungsplan (Umsetzungssteuerung)

## Zweck
Diese Roadmap operationalisiert den bisherigen Dossier-Stand in konkrete Umsetzungsblöcke mit klaren Deliverables, Akzeptanzkriterien und Reihenfolge. Grundlage ist die SSoT-Priorität aus `docs/README_DOSSIER_INDEX.md`.

## Leitplanken (immer aktiv)
- Kein API- oder Release-Vertrag mehr als Zielversprechen schreiben, ohne ihn auch zu implementieren.
- Keine neuen Core-Logik-Änderungen ohne passende Regression (Golden Case + Unit/Integration).
- Determinismus: gleicher Input + gleicher `config_hash` + gleiches `ruleset` → identische Ergebnisse.
- Daten-Integritätspfad immer aktiv: `unique_event_id`, `config_hash`, `report_integrity_id`.
- UX ist Workflow-gesteuert: Integrationen hinzufügen → Daten laden → Portfolio-Set prüfen → Steuerlauf-Wizard → Export.

## Aktueller Umsetzungsstand
- `GET /api/v1/report/files/{run_id}` ist implementiert und liefert JSON/CSV/PDF-Artefakte nach Scope.
- `GET /api/v1/report/export` unterstützt JSON, CSV und PDF; PDF-Dateien werden in Teile mit maximal `100` Seiten geschnitten.
- Exportzeilen enthalten `report_integrity_id`, `config_hash` und `data_hash`.
- Tax Lines enthalten `lot_source_event_id` und `transfer_chain_id` für Lot-/Transfer-Nachvollzug im Export.
- Transfer-Chain-IDs werden über zusammenhängende Transfer-Matches deterministisch aggregiert, nicht nur über den direkten Match.
- Transfer-Review-Tabellen zeigen Chain-ID und direkten Depot-Pfad als sichtbare Spur.
- `GET /api/v1/audit/transfer-chain/{transfer_chain_id}` liefert die vollständige Transferketten-Detailspur inklusive Wallet-Pfad, Assets, Zeitraum, Einzelschritten und Haltefrist-Fortführung.
- Die UI kann Transfer Chains aus Transfer-Review und Haupt-Transfer-Ledger direkt öffnen und als prüfbare Timeline anzeigen.
- `POST /api/v1/process/compare-rulesets` ist ergänzend zum GET-Endpunkt implementiert.
- `GET /api/v1/import/jobs` nutzt persistierte Importquellen und unterstützt Filter nach `integration` und `status`.
- Die UI zeigt Export-Artefakte im Steuer-Tab als klickbare Karten und bietet Ruleset-Vergleich sowie Snapshot-Erstellung an.
- Die UI bietet eine nicht-destruktive Snapshot-Vorschau mit Integritätsdaten, Zeilenzahlen und Beispielzeilen.
- Snapshot-Restore ist als nicht-destruktiver Restore-Plan umgesetzt: Vergleich von Snapshot-Run, aktuellem Run, Report-Integrity, Data-Hash und Config-Hash ohne Überschreiben aktueller Daten.
- Ruleset-Change-Log ist umgesetzt: `GET /api/v1/rulesets/{ruleset_id}/{ruleset_version}/change-log` liefert Freigabe-/Änderungshistorie; die Admin-UI zeigt Status und Change Log.
- Golden-Hash-Verification ist drift-blockierend: `scripts/verify_integrity.py` vergleicht die Golden-Files gegen `tests/fixtures/golden/hashes.json` und schlägt bei Abweichung fehl.
- Integrity-Fingerprint ist vom Ruleset-Registry-Import entkoppelt; dadurch sind Integritäts-Tests isoliert lauffähig und vermeiden Import-Zyklen.
- Ruleset-Auswahl bevorzugt deterministisch das Jahres-Standardruleset (`DE-YYYY-v1.0`) und ignoriert Draft-Custom-Rulesets bei automatischer Datumsauflösung.
- Lot-Aging ist UI-ready: offene FIFO-Lots zeigen Menge, Anschaffungszeitpunkt, Haltedauer, Tage bis Steuerfreiheit, Fortschritt und Asset-Zusammenfassung.
- `GET /api/v1/process/options` liefert validierte Steuerlauf-Optionen fuer den Wizard.
- `POST /api/v1/process/preflight` prueft Importdaten, Ruleset, offene High-Issues, unmatched Transfers und Bewertungsabdeckung vor dem Lauf.
- Die UI fuehrt vor `POST /api/v1/process/run` automatisch einen Preflight aus und blockiert den Steuerlauf bei harten Blockern.
- Preflight-Blocker und Warnungen verlinken per Guided Action direkt zur passenden Korrekturansicht.
- Das Import-Aktivitätsprotokoll ist im Import-Hub als eigenes Modul mit Connector-/Statusfilter, Detailauswahl und Wiederholsprung sichtbar.
- Portfolio-Sets können Quellen/Integrationen zugeordnet bekommen und zeigen eine Set-spezifische Wertkurve.
- Integrationen haben einen steuerlichen Modus (`active`, `reference`, `disabled`); Preflight und Steuerlauf nutzen standardmäßig nur aktive Quellen, um Referenzimporte nicht doppelt zu zählen.
- Das Integrations-Konfliktcenter gruppiert starke Überschneidungen zwischen aktiven Primärquellen und Referenzimporten und schreibt diese zusätzlich als Review-Issues.
- Integrations-Konflikte können als Massenentscheidung verarbeitet werden: Referenz-Events ausschließen, Referenzquellen deaktivieren oder Referenzmodus bestätigen. Jede Entscheidung benötigt Pflichtgrund und Notiz.
- Das Cockpit zeigt offene Review-Issues als priorisierte Kacheln im Hauptbildschirm; Klick auf eine Kachel springt direkt in den gefilterten Review-Bereich.
- Review-Ignore und Review-Kommentare sind als auditierbare Endpunkte umgesetzt; Ausschlüsse verlangen Pflichtgrund und Notiz, Raw Events werden nicht gelöscht.
- Die Transaktionssuche kann Events direkt in den Korrektur-/Ausschlussdialog übernehmen.
- Versionierte Review-Actions sind umgesetzt: Zeitzonen-Korrekturen werden beim Steuerlauf angewendet; Merge/Split-Entscheidungen werden ohne RAW-Löschung auditierbar dokumentiert.
- Review-Merge/Split wird in der Steuer-Arbeitskopie angewendet: Merge annotiert Events mit gemeinsamer `economic_event_id`, Split ersetzt ein Rohereignis durch dokumentierte Teil-Events.
- Frontend-Fehlerausgaben sind vereinheitlicht: API-/Netzwerkfehler zeigen Pfad, HTTP-Status und Trace-ID in einem Bedienpanel statt roher Parse-/JSON-Fehler.
- Das Cockpit enthält eine Operations-Statusleiste für Solana-Backfill, Import-Aktivität und Steuerjobs inklusive RPC-Delay/Rate-Limit-Hinweis und direktem Sprung zur passenden Bedienseite.
- Import-Jobs liefern Statusgrund, Severity und Retry-Hinweis; die Import-Detailansicht zeigt diese Angaben direkt für manuelle Wiederholung oder Quellenprüfung.
- Dashboard-Bewertung nutzt Request-lokale FX-/Asset-Preis-Caches; weiterer Performance-Hebel bleibt die Aufteilung von `dashboard_overview` in kleinere, separat ladbare Widgets.
- Dashboard-Zeitraumsteuerung ist global verfügbar: Jahr im Kopfbereich wählen, Performance/Jahresanalyse/Portfolio-Verlauf und Steuerjahr laufen synchron.
- Erster Split-Endpunkt umgesetzt: `GET /api/v1/dashboard/shell` liefert schnelle Cockpit-Grunddaten, während die schwere Bewertungsübersicht nachgeladen werden kann.
- Widget-Split erweitert: `GET /api/v1/dashboard/yearly-activity` lädt Jahres-/Quellen-/Asset-Auswertung separat und optional jahresgefiltert; `GET /api/v1/dashboard/portfolio-history` lädt die Wertzeitreihe separat.
- Die UI ruft den monolithischen `dashboard_overview` nicht mehr im normalen Dashboard-Load auf, sondern rendert zuerst den Shell und aktualisiert Jahresanalyse/Portfolio-Verlauf asynchron nach.
- Nach Änderungen validiert: Ruff, Mypy für `src/tax_engine/api/app.py`, gezielte API-Regressionen und `node --check` für `app.js`.

## Sprint-1: Compliance- & API-Lücke schließen (Pflicht vor weiteren Features)
Ziel: Den technischen Funktionsumfang an die Roadmap-Dokumentation angleichen.

### 1.1 API-Contract vervollständigen
- Implementiere fehlende Endpunkte (falls nicht vorhanden):
  - `POST /api/v1/rulesets`
  - `GET /api/v1/rulesets`
  - `GET /api/v1/rulesets/{ruleset_id}/{ruleset_version}`
  - `GET /api/v1/integrity/report/{run_id}`
  - `GET /api/v1/integrity/event/{unique_event_id}`
  - `POST /api/v1/snapshots/create/{run_id}`
  - `GET /api/v1/snapshots/{snapshot_id}`
  - `GET /api/v1/process/compare-rulesets`
  - `POST /api/v1/compliance/classification/{run_id}`
- Prüfe und ergänze bestehende Endpunkte für fehlende Workflow-Teile (z. B. `ruleset_id`/`ruleset_version` im Run-Request und Ergebnisobjekt).

### 1.2 Integrationsstatus-Workflow
- Ergänze pro Integrationsimport einen persistierten Job-Header (`connector, started_at_utc, rows, duplicates, warnings, status`).
- Lege API für `GET /api/v1/import/jobs` und Filterung nach Integration/Status an.
- Standardisiere Meldungscode und Error-Codes in `StandardResponse`.

### 1.3 Review-Fähigkeiten vorbereiten
- Prüfe vorhandene Review-Logik auf Vollständigkeit:
  - Issue-Priorisierung (Blocker/Warnungen)
  - Nachvollziehbare Resolver-Historie
  - Transfer-Recon-Bestätigung mit Nachweis
- Falls noch nicht stabil: `manual merge/split/ignore` als explizit versionierte Admin-Aktion ergänzen.

### 1.4 DB-Modell auf Integrität erweitern
- Prüfe/ergänze Tabellen:
  - `event_fingerprints`
  - `ruleset_history`
  - `report_integrity`
  - `snapshots`
  - `ruleset_catalog` (falls nicht existent)

**Acceptance Criteria Sprint-1**
- SSoT-Endpunkte sind in API-Aufzählung implementiert und in Tests nachweislich erreichbar.
- Fehlende Roadmap-Route liefert kein unvollständiges 404-Silence mehr.
- Review-Flow kann mindestens einen vollständigen Reconcile-Block ohne manuellen Workaround schließen.

## Sprint-2: Kern-Funktionslücke Export/Reporting + Lot-Nachvollzug
Ziel: Nutzer bekommt belastbares Endprodukt statt technischer Rohdatenansicht.

### 2.1 Export-Engine
- Implementiere Export-API:
  - `GET /api/v1/report/export` (CSV/JSON/PDF)
  - `GET /api/v1/report/files/{run_id}`
- Ergänze 100-Seiten-Splitting bei PDF-Ausgabe.
- In jeder PDF-Seite: Report-Integrity-ID + Lauf-Metadaten + Konfig-/Ruleset-Referenz.

### 2.2 Tax-Lot-Nachvollzug & Visualisierungsvorlagen
- Ergänze JSON-Exportfelder:
  - `ruleset_id`, `ruleset_version`, `report_integrity_id`, `config_hash`, `data_hash`
  - `lot_id`, `lot_opened_at`, `lot_source_event_id`, `transfer_chain_id`
- Definiere standardisierte Spalten für Portfolio-Ansicht (Bestand, Durchschnittsbestand, Holding-Alter).

### 2.3 Timeline/Alterung auf Asset-Lot-Ebene
- Ergänze API/Service, das Haltedauer-Verteilungen ausgibt:
  - Beispielstruktur: `[{ asset, qty, holding_days, acquisition_date, open_lot_id }]`
- Nutze bereits vorhandene offene Lot-Sicht als Basis (`build_open_lot_aging_snapshot`) und erweitere auf UI-ready JSON.
- Stand: umgesetzt mit `days_to_exempt`, `holding_progress_ratio`, Asset-Summen, steuerfreier Menge und steuerpflichtiger Menge.

**Acceptance Criteria Sprint-2**
- PDF und CSV exportierbar und wiederholbar.
- `report_integrity_id` in jedem Export-/Tax-Line vorhanden.
- Haltefristen können je Asset in klarer Struktur geprüft werden (keine nur „JSON-Ansicht“ mehr).

## Sprint-3: Produktivfokus & UX-Vereinfaltung
Ziel: Das System wird benutzbar wie ein Steuer-Tool (nicht nur wie eine Import-API).

### 3.1 UX als Integrationen-Workflow
- Frontend-Fluss aufbauen:
  1. Integrationen auswählen/konfigurieren
  2. Vollimport oder Delta-Import auslösen
  3. Portfolio-Set bilden
  4. Preflight starten
  5. Steuerlauf per Wizard (ohne Freitext)
  6. Export
- Reduziere technische Einzelansichten; nutze modulare Sektionen mit klarer Reihenfolge.

### 3.2 Portfolio- und Verlauf-Ansichten
- Implementiere zentrale Widgets:
  - Gesamtwert (EUR)
  - Asset-Allokation
  - Historie (Zeitachse)
  - Quellenbeitrag je Integration
- Zeige offene Issues direkt im Hauptbildschirm als Prioritäts-Pile.
- Stand: Issue-Pile im Cockpit umgesetzt, inkl. direktem Sprung in den gefilterten Review-Bereich.

### 3.3 Rollen-/Steuerlogik im Frontend
- Rollenerkennung (`auto/private/business`) als UI-Schaltfläche mit Überschreibmöglichkeit.
- Bei `business`/`mixed` passende Hilfetexte + Pflichtreview-Kette.

### 3.4 Verfügbarkeits- und Limit-Failover UX
- RPC- und API-Connector-Fails müssen im UI als laufender Job-Status angezeigt werden, inkl. Ursache und Retry-Option.
- Einheitliches Fehlerfenster statt roher JSON/HTTP-Textausgaben.
- Stand: Einheitliches Fehlerpanel und Cockpit-Operations-Status umgesetzt; Connector-spezifische Retry-Steuerung bleibt nächster Ausbau.

**Acceptance Criteria Sprint-3**
- Nutzer kann mit Standardfall (1 Integration + 1 Export) vollständig arbeiten, ohne Roh-API-Schritte.
- Die wichtigste Datenhistorie ist visuell erkennbar (Portfolio, Verlauf, offene Punkte).

## Sprint-4: Revisionssicherheit, Side-by-Side, Release-Zuverlässigkeit
Ziel: Steuer-/Prüfungssicherheit auf Produktionsniveau.

### 4.1 Ruleset-Vergleich
- Implementiere Vergleichsrun mit identischem Input, zwei Rulesets (und klarer Differenz-Bericht).
- `rule_change_log` inkl. Freigabestatus (`draft/approved/deprecated`) anzeigen.
- Stand: umgesetzt als Ruleset-Change-Log-Endpunkt plus Admin-Ansicht für Status und Änderungshistorie.

### 4.2 Snapshot- und Versionsmanagement
- Snapshot-Workflow in UI und API verankern:
  - Erstellung aus finalisiertem Run
  - Wiederherstellungsvorschau für früheren Berichtsstand
- Dokumentiere Kettenstand (`V1 -> V2 ...`) bei Änderungen nach Finalisierung.

### 4.3 Golden Case Drift & CI-Härtung
- Golden-Case-Pipeline erzwingen als `required check` für alle Kernmodule.
- Stand: `Golden Hash Verification` ist in CI vorhanden und vergleicht gegen explizite Referenz-Hashes.
- CI-Gates auf Zielwerte anheben, sobald ausreichend stabil:
  - FIFO/Kern ≥95
  - API ≥80
  - UI ≥70
- Branch-Protection prüfen/setzen (kein Direkpush auf `main`, erforderliche Checks).

**Acceptance Criteria Sprint-4**
- Side-by-Side-Ergebnis ist reproduzierbar und dokumentiert.
- Snapshot kann im Sinne einer Nachprüfung geladen werden.
- CI ist nicht mehr „nur grün“, sondern inhaltlich auf Kernqualität abgefangen.

## Roadmap-Umsetzungstempo (Vorschlag)
- Sprintdauer: 2 Wochen je Sprint.
- Definition of Done je Sprint:
  - Tests grün
  - Goldentest mindestens 1 repräsentativer Fall
  - Changelog-Eintrag
  - Dokumentation im Dossier aktualisiert

## Offene Risiken
- Exchange-API-Lücken (v. a. Binance/Konto-/Historienlücken): ggf. CSV-Fallback verpflichtend.
- Solana Public RPC Instabilität: Key-basierter RPC-Profil-Standard empfohlen.
- UI-Angemessenheit bei 30k+ Zeilen: Performance mit virtualisierten Tabellen erforderlich.

## Nächste konkrete Arbeitspakete (Backlog)
1. Snapshot-Wiederherstellungsworkflow mit explizitem, nicht destruktivem Restore-Plan modellieren: umgesetzt als `POST /api/v1/snapshots/restore-plan/{snapshot_id}`.
2. Review-Merge/Split fachlich auf die Steuer-Arbeitskopie anwenden: Basis umgesetzt, connector-spezifische Feinschemata bleiben Erweiterung.
3. Integrations-Konfliktcenter um manuelle Massenentscheidung erweitern: umgesetzt für markierte Konfliktgruppen mit `exclude_reference_events`, `disable_reference_sources` und `confirm_reference_only`.
4. Transfer-Chain-Detailansicht ergänzen: vollständige mehrstufige Timeline pro Chain-ID statt nur direkter Zeile.
