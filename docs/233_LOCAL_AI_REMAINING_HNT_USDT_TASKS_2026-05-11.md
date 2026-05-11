# Auftrag fuer lokale KI: verbleibende HNT-/USDT-Restluecken

Stand: 2026-05-11

## Ziel

Die lokale KI soll die letzten offenen HNT-/USDT-Restluecken read-only untersuchen und konkrete, belegbare naechste Schritte liefern.

Aktueller Stand nach den letzten Fixes:

- Restzeilen: `6`
- Rest-Erloes: `2189.09067462794969078534501 EUR`
- 2022-HNT-Zero-Cost ueber `50 EUR`: `0`
- Verbleibend:
  - 2021 HNT: `3` Zeilen, `805.2140123327466767853450105 EUR`
  - 2022 USDT: `3` Zeilen, `1383.876662295203014 EUR`

Primarquellen fuer den aktuellen Stand:

- `docs/229_HNT_USDT_REMAINING_INVENTORY_GAP_AUDIT_2026-05-11.md`
- `docs/224_VALUATION_ANOMALY_AUDIT_RESULTS_2026-05-11.md`
- `docs/230_FAIRSPOT_HNT_LEGACY_TRANSFER_TRACE_2026-05-11.md`
- `docs/231_HNT_LEGACY_SELF_WALLET_TRANSFER_MATCH_2026-05-11.md`
- `docs/232_BINANCE_TXHIST_STABLE_COUNTERFLOW_HNT_FIX_2026-05-11.md`

## Harte Regeln

Die lokale KI darf:

- nur read-only analysieren,
- lokale Rohdaten lesen,
- die AI-Readonly-DB abfragen,
- Event-IDs, Source-Files, Zeitpunkte, Mengen und Gegenbuchungen dokumentieren,
- konkrete technische Fix-Vorschlaege machen,
- neue Auditberichte als Vorschlag unter `var/` oder in einem getrennten Ergebnisbericht schreiben.

Die lokale KI darf nicht:

- Anschaffungskosten, Kurse, FX-Raten oder steuerliche Behandlung schaetzen,
- Transferwerte als Anschaffungskosten verwenden,
- Rohdaten loeschen, veraendern oder ueberschreiben,
- Review-Issues schliessen,
- DB-State veraendern,
- `var/`, CSV, XLSX, DB, SQLite oder Secrets committen,
- historische offene Issues verstecken, nur damit ein Gate gruen wird.

Jeder gefundene technische Fix muss unterscheiden zwischen:

- deterministischer Fix,
- belegter Import- oder Match-Vorschlag,
- reine Belegluecke,
- fachliche Review-Entscheidung.

## Datenzugriff

Readonly-DB:

```bash
sqlite3 'file:/root/.local/share/steuerreport/ai_readonly/steuerreport_ai_readonly.sqlite?mode=ro&immutable=1'
```

Wichtige Tabellen/Views:

- `ai_open_zero_cost_tax_lines`
- `ai_tax_lines_flat`
- `ai_raw_events_flat`
- `ai_transfer_matches_flat`
- `raw_events`
- `source_files`
- `transfer_matches`
- `fx_cache`

## Auftrag 1: 2022 USDT Opening-/Bot-Historie

Prioritaet: hoch, weil groesster Restbetrag.

Betroffene Zeilen aus dem aktuellen Audit:

| Jahr | Line | Asset | Menge | Erloes EUR | Quelle | Lot-Quelle |
| ---: | ---: | --- | ---: | ---: | --- | --- |
| 2022 | 412 | `USDT` | 75.1046222062 | 66.352680580511514 | `binance/trade/out` | leer |
| 2022 | 442 | `USDT` | 168.7646835 | 148.757630271075 | `pionex/trade/out` | leer |
| 2022 | 514 | `USDT` | 1325.95876277 | 1168.7663514436165 | `pionex/trade/out` | leer |

Aufgabe:

1. Zu jeder Zeile `source_event_id`, Source-File, Row-Index und Raw-Payload ermitteln.
2. Zeitnahe Events derselben Plattform am gleichen Timestamp und im Umfeld von plus/minus 24 Stunden pruefen.
3. Fuer Pionex gezielt pruefen:
   - Opening-Balance-Hinweise,
   - Bot-/Grid-Historie,
   - doppelte Pionex-Quellen,
   - interne Pionex-Transfers,
   - USDT-Zufluesse vor den Sell-/Spend-Zeilen.
4. Fuer Binance gezielt pruefen:
   - Transaction-History-Gruppe am `2022-01-05T15:36:46+00:00`,
   - ob der verbleibende USDT-Abgang selbst eine Anschaffungskette aus frueherem USDT-Bestand braucht,
   - ob ein belegter Stable-/EUR-Gegenfluss existiert.
5. Ergebnis je Zeile:
   - `belegbarer_fix`,
   - `moeglicher_import`,
   - `nur_review_entscheidung`,
   - `offene_belegluecke`.

Erwartetes Ergebnis:

- Tabelle je USDT-Zeile mit:
  - `tax_year`
  - `line_no`
  - `source_event_id`
  - `source_file`
  - `row_index`
  - `tx_id`
  - `timestamp_utc`
  - `quantity`
  - `candidate_source_event_ids`
  - `Bewertung`
  - `naechster_sicherer_schritt`

## Auftrag 2: 2021 HNT Restbelege

Betroffene Zeilen:

| Jahr | Line | Asset | Menge | Erloes EUR | Quelle | Lot-Quelle |
| ---: | ---: | --- | ---: | ---: | --- | --- |
| 2021 | 1285 | `HNT` | 22.7759533567933520993873 | 445.1808341476849715363131107 | `binance/trade/out` | leer |
| 2021 | 1347 | `HNT` | 14.651308409999999970498 | 290.1121724005967814158276469 | `binance/trade/out` | `binance_api/deposit/in` |
| 2021 | 1517 | `HNT` | 3.536102305597830579502 | 69.92100578446492383320425294 | `binance/trade/out` | `binance_api/deposit/in` |

Aufgabe:

1. Fuer `2021-08-17T16:10:05+00:00` erneut Binance-HNT-Bestand und lokale Binance-History pruefen.
2. Fuer `2021-08-20` die Kette um Deposit `dd5353eedbee68d33a5c687e013b67f468dac6a769af6b56b60dfd7c1e40fa2f` pruefen.
3. Legacy-HNT-Quellen pruefen:
   - `helium_legacy_cointracking`
   - `helium_legacy_raw`
   - `heliumtracker`
   - lokale Excel-/CSV-Historie
   - Fairspot-Trace aus `docs/230_...`
4. Keine Bewertung aus `value_usd` eines Transfers ableiten.
5. Falls Mining-/Reward-Bestand als Cost-Basis genutzt werden soll, muss der konkrete Reward-Event mit Menge, Timestamp und Bewertung vorhanden sein.

Erwartetes Ergebnis:

- Je HNT-Zeile klare Einordnung:
  - belegter Vorbestand gefunden,
  - Transfer-Match fehlt,
  - Importquelle fehlt,
  - Beleg reicht nicht,
  - fachliche Review-Entscheidung erforderlich.

## Auftrag 3: Abschluss- und Gate-Pruefung nach jedem Vorschlag

Wenn die lokale KI einen technischen Fix vorschlaegt, muss sie auch angeben, welche Validierung danach laufen soll:

```bash
python3 scripts/build_ai_readonly_db_snapshot.py
python3 scripts/hnt_usdt_remaining_inventory_gap_audit_20260511.py
python3 scripts/valuation_anomaly_audit_20260511.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 scripts/verify_integrity.py --all-years
```

Bei Codefix zusaetzlich:

```bash
python3 -m ruff check src/ tests/ scripts/ --no-cache
python3 -m mypy src/ --cache-dir=/tmp/steuerreport_mypy_cache
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest -q tests/unit
```

## Ausgabeformat

Die lokale KI soll am Ende einen kompakten Bericht erstellen:

```text
Titel:
Datum:
Verwendete Datenbasis:
Gepruefte Zeilen:
Gefundene Kandidaten:
Deterministische Fixes:
Nicht belegbare Luecken:
Fachliche Review-Fragen:
Empfohlene naechste Commits:
Validierungsbefehle:
```

Keine Rohdaten in den Bericht kopieren. Nur abgeleitete Fakten, Event-IDs, Mengen, Zeitpunkte, Dateinamen und Zeilennummern dokumentieren.
