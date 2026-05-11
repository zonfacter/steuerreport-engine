# Plan: Bewertungsfehler und aehnliche Fehler systematisch finden

Stand: 2026-05-11

## Ziel

Der SOL-Fall vom `2025-01-04` war kein klassischer Zero-Cost-Fund, sondern eine
materiell falsche Fast-Null-Kostenbasis. Ziel dieses Plans ist daher nicht nur,
exakte Nullkosten zu finden, sondern auch aehnliche Bewertungsfehler:

- Swap-In ohne passenden Preisanker.
- Transfer-Event, das semantisch ein Swap ist.
- Fast-Null-Kostenbasis mit erheblichem Erloes.
- Kostenbasis, die nur aus Fee besteht.
- Fehlende oder falsche Ableitung aus Gegenfluss, FX-Cache oder Referenzquelle.
- Auffaellige Gewinn-/Kostenbasis-Relationen im aktuellen Export.

Alle Befunde muessen gegen Rohdaten, FX-Cache, vorhandene Referenzen oder
Review-Actions belegt werden. Keine Preise, FX-Kurse oder steuerlichen
Behandlungen duerfen erfunden werden.

## Leitprinzipien

- Rohdaten bleiben unveraendert.
- Korrekturen erfolgen nur ueber Code, dokumentierte Overrides, Review-Actions,
  Transfer-Matches, Preis-/FX-Backfills mit Quelle oder Audit-Skripte.
- Automatisch geschlossen wird nichts, was eine Beleg- oder Steuerentscheidung
  braucht.
- Jeder Fix bekommt mindestens einen Regressionstest.
- Nach jedem Fix wird das betroffene Steuerjahr neu gerechnet und der
  AI-Readonly-Snapshot aktualisiert.
- Exportfaehigkeit wird job-spezifisch gegen Review-Gate, PDF-Seitenlimit und
  Report-Zeilen validiert.

## Phase 1: Anomalie-Audit bauen

Ein neues Audit-Skript soll angelegt werden:

```text
scripts/valuation_anomaly_audit_20260511.py
```

Lokale JSON-Ausgabe:

```text
var/valuation_anomaly_audit_2026-05-11.json
```

Dokumentierter Ergebnisbericht:

```text
docs/224_VALUATION_ANOMALY_AUDIT_RESULTS_2026-05-11.md
```

Das Skript soll die neuesten abgeschlossenen Jobs je Steuerjahr `2020` bis
`2026` auswerten und mindestens diese Befundklassen erzeugen.

## Befundklasse A: Fast-Null-Kostenbasis

Pruefung:

```text
proceeds_eur > 10 EUR
cost_basis_eur > 0
cost_basis_eur / proceeds_eur < 0.005
tax_status in taxable, business
```

Begruendung:

Exakte Nullkosten werden bereits ueber `ai_open_zero_cost_tax_lines` sichtbar.
Der SOL-Fall lag aber knapp oberhalb Null und war dadurch nicht im Gate.

Ausgabe je Treffer:

- Steuerjahr, Job, Line-No.
- Asset, Menge, Kauf-/Verkaufszeit.
- Kostenbasis, Erloes, Ergebnis.
- Source-Event-ID und Lot-Source-Event-ID.
- Raw-Event-Typ, Source, Side, `defi_label`, `tx_id`.
- Hinweis, ob ein FX-Kurs fuer das Asset am Kauftag vorhanden ist.
- Hinweis, ob im selben `tx_id` ein bepreister Gegenfluss existiert.

## Befundklasse B: Swap-Semantik ohne Preisanker

Pruefung auf Raw-Events:

```text
source=solana_rpc
side=in
defi_label=swap
event_type in sol_transfer, token_transfer, swap_in_aggregated
price_usd empty
price_eur empty
value_usd_sum empty
value_eur empty
```

Zusaetzliche Kandidaten:

- `event_type` enthaelt `swap`.
- Raw-Payload enthaelt Jupiter-/DEX-/Route-Hinweise.
- Gleiches `tx_id` hat einen Outflow mit anderem Asset.

Begruendung:

Der SOL-Fehler entstand, weil `defi_label=swap` vorhanden war, aber der native
Event-Typ nicht in der Preisanker-Whitelist stand.

## Befundklasse C: Gegenfluss vorhanden, Inflow unbewertet

Pruefung je `tx_id`:

- Mindestens ein Inflow ohne Preis-/Wertanker.
- Mindestens ein Outflow mit Asset ungleich Inflow-Asset.
- Outflow-Asset ist Stablecoin oder hat FX-Cache `Asset/USD` am Ereignistag
  oder davor.

Ergebnis:

- Kandidat fuer `same_tx_priced_counterflow`.
- Erwarteter USD-Wert aus Gegenfluss als Plausibilitaet.
- Keine automatische Uebernahme ohne Codepfad- oder Datenbeleg.

## Befundklasse D: Asset-FX vorhanden, aber Lot unbewertet

Pruefung:

- Lot-Source-Event hat `side=in`.
- Asset hat FX-Cache `Asset/USD` am Datum oder davor.
- Lot fuehrt spaeter zu Tax-Line mit Kostenbasis nahe Null.

Begruendung:

Wenn ein vorhandener Kurs nicht genutzt wird, liegt wahrscheinlich ein
Klassifikations- oder Event-Type-Problem vor.

## Befundklasse E: Auffaellige Gewinnquote

Pruefung:

```text
proceeds_eur >= 50 EUR
gain_loss_eur / proceeds_eur > 0.95
hold_days < 365
```

Priorisierung:

- Hoch: gleichzeitige Kostenbasis < `1 EUR`.
- Mittel: Kostenbasis zwischen `1 EUR` und `5%` des Erloeses.
- Niedrig: Asset mit bekannt hoher Volatilitaet, aber belegter Kostenbasis.

Diese Klasse ist ein Suchfilter, kein Beweis fuer Fehler.

## Phase 2: Ergebnisse priorisieren

Prioritaet 1:

- Aktuelle Jahre `2024`, `2025`, `2026`.
- Steuerpflichtige oder Business-Zeilen.
- Erloes ab `50 EUR`.
- Kostenbasis unter `1%` des Erloeses.
- Inflow-Event hat Swap-Semantik oder bepreisten Gegenfluss.

Prioritaet 2:

- Historische offene Jahre `2020` bis `2023`.
- Exempt-Zeilen mit grosser Kostenbasisabweichung, weil sie Inventar und
  spaetere FIFO-Lots beeinflussen koennen.

Prioritaet 3:

- Kleinstwerte unter `10 EUR`, nur sammeln und im Bericht ausweisen.

## Phase 3: Deterministische Fix-Regeln ableiten

Jeder Kandidat wird einer dieser Kategorien zugeordnet.

### Kategorie 1: Codepfad fehlt

Beispiel:

```text
sol_transfer + defi_label=swap wurde nicht als Swap-In erkannt
```

Vorgehen:

- Enge Bedingung im bestehenden Preisanker-/Processing-Code erweitern.
- Regressionstest mit minimalem Raw-Event.
- Kein breiter Refactor.

### Kategorie 2: Preis-/FX-Daten vorhanden, aber nicht genutzt

Vorgehen:

- Klaeren, welcher Codepfad den vorhandenen Kurs ignoriert.
- Fix bevorzugt in Enrichment-/Valuation-Schicht.
- Test prueft, dass `price_usd`, `value_usd_sum` oder EUR-Kostenbasis gesetzt
  wird.

### Kategorie 3: Gegenfluss bepreist, Inflow unbekannt

Vorgehen:

- Bestehende `same_tx_priced_counterflow`- oder `raw_priced_route_counterflow`
  Logik erweitern.
- Nur gleiche Transaktion und klare Gegenrichtung verwenden.
- Keine Summen aus unsicheren Routen erfinden.

### Kategorie 4: Belegluecke

Vorgehen:

- Kein automatischer Fix.
- Issue/Review-Hinweis offen lassen.
- Benoetigte Quelle benennen, zum Beispiel Exchange-Trade-History,
  Solscan/Jupiter-Export, API-Support-Export oder FX-Quelle.

### Kategorie 5: Steuerliche Entscheidung

Vorgehen:

- Kein automatischer Fix durch Agent.
- Als manuelle Review-Entscheidung dokumentieren.
- Export-Gate nur dann freigeben, wenn vorhandene Projektregeln das tragen.

## Phase 4: Re-Processing und Validierung

Nach jedem Fix:

1. Betroffenes Steuerjahr neu rechnen.
2. Befundklasse erneut laufen lassen.
3. Konkrete alte und neue Tax-Line gegenueberstellen.
4. `ai_open_zero_cost_tax_lines` pruefen.
5. Job-spezifisches Review-Gate pruefen.
6. Report-Dateien und PDF-Seitenlimit pruefen.
7. AI-Readonly-Snapshot neu bauen.
8. Handoff und Ergebnisbericht aktualisieren.

Mindestchecks:

```text
python3 -m ruff check <geaenderte Dateien> --no-cache
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest <gezielte Tests>
python3 -m mypy src/ --cache-dir=/tmp/steuerreport_mypy_cache
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 scripts/verify_integrity.py --all-years
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 scripts/build_ai_readonly_db_snapshot.py
```

Bei groesserem Codeumfang zusaetzlich:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest -q tests/unit
COVERAGE_FILE=/tmp/steuerreport-api-coverage PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest -p no:cacheprovider tests/unit/api --cov=src/tax_engine/api --cov-fail-under=80 -q
node --check src/tax_engine/ui/static/app.js
```

## Phase 5: Dauerhafte Schutzmechanismen

Nach dem initialen Audit sollen die wichtigsten Pruefungen dauerhaft in den
Workflow.

### Neuer Integrity-Check

`scripts/verify_integrity.py` soll optional um eine Bewertungsanomalie-Pruefung
erweitert werden oder ein separates Gate-Skript erhalten:

```text
scripts/verify_valuation_sanity.py
```

Dieses Gate darf nicht jeden kleinen Treffer blockieren. Blockieren soll es nur:

- aktuelle Steuerjahre,
- steuerpflichtige/Business-Zeilen,
- Erloes ab definierter Materialitaet,
- Kostenbasis extrem niedrig,
- vorhandener belegbarer Preisanker wurde offensichtlich nicht genutzt.

### Review-Gate-Erweiterung

Das Review-Gate soll mittelfristig neben exakten Zero-Cost-Zeilen auch
`near_zero_cost_material` ausweisen:

```text
cost_basis_eur / proceeds_eur < 0.005
proceeds_eur >= 50
```

Das soll zunaechst als Warnung starten. Erst nach Kalibrierung darf daraus ein
Blocker fuer aktuelle Jahre werden.

### Dashboard-Sicht

Die Issue-Inbox soll eine neue Kategorie anzeigen:

```text
valuation_anomaly
```

Wichtige Felder:

- Scope current/historical.
- Asset.
- Steuerjahr.
- Erloes.
- Kostenbasis.
- Quote Kostenbasis/Erloes.
- Verdacht: `near_zero_cost`, `swap_without_anchor`,
  `priced_counterflow_available`.

## Konkrete naechste Arbeitspakete

1. Audit-Skript `scripts/valuation_anomaly_audit_20260511.py` implementieren.
2. Bericht `docs/224_VALUATION_ANOMALY_AUDIT_RESULTS_2026-05-11.md` erzeugen.
3. Treffer fuer `2025` priorisieren und Top-Kandidaten manuell gegen Raw-Events
   pruefen.
4. Deterministische Fixes einzeln umsetzen, testen, neu rechnen und
   dokumentieren.
5. Wenn die Heuristiken stabil sind, `verify_valuation_sanity.py` als dauerhaftes
   Gate ergaenzen.
6. Danach Review-Gate und Dashboard um `near_zero_cost_material` erweitern.

## Stop-Regeln

Der Agent muss stoppen und dokumentieren, statt automatisch zu fixen, wenn:

- kein vorhandener Preis-/FX-/Gegenfluss-Beleg existiert,
- mehrere moegliche Gegenfluesse in derselben Transaktion nicht eindeutig sind,
- der Befund eine steuerliche Einordnung statt eine technische Bewertungsluecke
  betrifft,
- eine Korrektur Rohdaten veraendern wuerde,
- ein Fix aktuelle Exportfaehigkeit verschlechtert oder neue Gate-Blocker
  erzeugt.

## Erfolgskriterien

Der Plan gilt als abgearbeitet, wenn:

- alle aktuellen Jahre `2024` bis `2026` auf Fast-Null- und Swap-Anomalien
  geprueft sind,
- alle deterministisch belegbaren Fehler behoben und neu gerechnet sind,
- verbleibende Treffer als Belegluecke oder manuelle Review-Entscheidung
  dokumentiert sind,
- der 2025-Export weiterhin `allow_export=true` hat,
- PDF-Seiten je Datei weiter unter `100` bleiben,
- die AI-Readonly-DB den neuesten validierten Stand enthaelt,
- der Schutz gegen aehnliche Fehler als wiederholbares Skript oder Gate
  verfuegbar ist.
