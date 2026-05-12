# Chronological Platform Ledger Plan - 2026-05-09

## Ziel

Alle vorhandenen Transfers, Trades, Fees, Rewards und Referenz-/Primaerquellen werden in ein chronologisches, plattformbezogenes Ledger ueberfuehrt. Daraus sollen pro Plattform virtuelle Bestaende nachsimuliert und gegen heutige API-/CSV-Snapshots abgeglichen werden.

Das Ziel ist nicht, neue steuerwirksame Buchungen zu erraten, sondern:

- echte Transferketten sichtbar machen,
- Plattformbestaende historisch rekonstruieren,
- fehlende Quellen/Opening-Balances quantifizieren,
- der lokalen KI ein sauberes, kompaktes Analyseformat geben,
- final nachvollziehbare Review-Entscheidungen vorbereiten.

## Grundprinzip

Die Datenbank bleibt append-only: RAW-Daten werden nicht geloescht. Korrekturen laufen weiter ueber Overrides, Review-Actions, Ignored-Tokens und Review-Kandidaten.

Neue Ebene: `platform_ledger`

Eine Zeile ist eine saldenwirksame Bewegung auf einer konkreten Plattform oder Wallet:

- `timestamp_utc`
- `asset`
- `platform`
- `account_scope`
- `event_id`
- `source`
- `event_type`
- `side`
- `quantity_delta`
- `fee_asset`
- `fee_delta`
- `tx_id`
- `counterparty_platform`
- `counterparty_address`
- `transfer_group_id`
- `confidence`
- `evidence_refs`
- `review_status`

## Plattform-Simulation

Der Simulator berechnet pro Plattform und Asset:

- Startbestand
- laufender Bestand nach jeder Bewegung
- erster negativer Bestand
- schlimmster negativer Bestand
- Endbestand laut Ledger
- heutiger Ist-Bestand laut API/CSV/Snapshot
- Differenz Ledger zu Ist
- benoetigtes Opening-Inventar, wenn kein Start-Snapshot existiert

Wichtig: Global saubere Bestaende reichen nicht. Ein Transfer von Binance zu Pionex muss auf Binance `out` und auf Pionex `in` passen. Sonst ist die Gesamtbilanz zufaellig sauber, aber die Plattform-Chronologie nicht.

## Transfer-Pairing

Transfergruppen werden in Stufen gebaut:

1. Exakter Match:
   - gleiche `tx_id`,
   - gleiche Asset-Menge oder Menge minus Fee,
   - bekannte Plattform-/Wallet-Adresse.
2. Address-Match:
   - Binance/Bitget/Pionex/Solana/Helium bekannte Ziel- oder Deposit-Adressen,
   - Zeitfenster je Chain.
3. Amount-Time-Match:
   - gleicher Assetbetrag,
   - plausibles Zeitfenster,
   - Richtung `withdrawal/out` zu `deposit/in`.
4. Semantic-Match:
   - vorhandene Kommentare, Raw Labels, Integration Names,
   - z.B. `FIAT Payments`, `TRC20`, `HNT`, `staking wallet`.
5. KI-Vorschlag:
   - nur fuer Kandidatenliste und Priorisierung,
   - niemals automatisch steuerwirksam.

## Lokale KI-Unterstuetzung

Die lokale KI bekommt keine komplette Datenbank roh, sondern kompakte Analysepakete:

- ungepaarte Transfers,
- negative Plattform-Balance-Fenster,
- bekannte Adressen,
- aggregierte Tages-/Stunden-Netze,
- Belegketten mit maximal relevanten Zeilen,
- aktuelle API-Snapshots.

Provider:

- `llama-cpp-classifier`
- Endpoint: `http://192.168.2.203:11435/v1/chat/completions`
- Modell laut aktuellem Setup: `qwen3.6-35b-a3b-iq4xs`
- `enable_thinking=false`, JSON-only Output.

KI-Ausgabeformat:

```json
{
  "hypothesis": "short description",
  "confidence": "low|medium|high",
  "matched_event_ids": ["..."],
  "missing_evidence": ["..."],
  "recommended_action": "no_action|request_source|create_review_candidate|exclude_reference_duplicate",
  "must_not_auto_book": true
}
```

## Umsetzungsschritte

### Phase 1 - Ledger-Export

Script: `scripts/build_platform_ledger.py`

Aufgaben:

- Effektive Events laden.
- Token-Aliase, Ignored-Tokens, Overrides beachten.
- Bewegungen aus `chronological_balance_break_audit.py` wiederverwenden.
- Plattform aus `source`, `raw_row`, `Integration Name`, Adresse und Connector ableiten.
- JSONL/CSV erzeugen:
  - `var/platform_ledger_2026-05-09.jsonl`
  - `var/platform_ledger_2026-05-09.csv`
  - `docs/130_PLATFORM_LEDGER_EXPORT_2026-05-09.md`

### Phase 2 - Transfergruppen

Script: `scripts/match_platform_transfers.py`

Aufgaben:

- Exakte TXID-Paare bilden.
- Bekannte Adressen einbeziehen:
  - Pionex TRC20 Deposit `TMHP82UVnvYQTqoxEP98gVch5DqbzZYfCQ`
  - Binance HNT Deposit `138bCXPVfSq7yyTfoDUrVwztPmUr4WGyA7TED9Y41djmF7rjA8y`
  - Solana Wallet `wBrPoiEEzKYwH6obgAmNAC2iskiNs4HvwoAwqJbV2oB`
  - weitere Adressen aus `docs/93_CEX_SOLANA_ADDRESS_CROSS_AUDIT_2026-05-09.md`
- Transfergruppen speichern:
  - `var/platform_transfer_groups_2026-05-09.json`
  - `docs/131_PLATFORM_TRANSFER_GROUPS_2026-05-09.md`

### Phase 3 - Plattform-Bestandssimulation

Script: `scripts/simulate_platform_balances.py`

Aufgaben:

- Ledger nach `platform + asset + timestamp` sortieren.
- Laufende Bestaende berechnen.
- Negative Fenster ausweisen.
- Benoetigtes Opening-Inventar je Plattform/Asset berechnen.
- Ausgabe:
  - `var/platform_balance_simulation_2026-05-09.json`
  - `docs/132_PLATFORM_BALANCE_SIMULATION_2026-05-09.md`

Sonderfokus:

- Pionex `USDT`, `HNT`, `MXC`, `BUSD`
- Binance `HNT`, `USDT`, `EUR`
- Bitget `USDT`, `HNT`, `SOL`
- Solana Wallet `SOL`, `USDC`, `USDT`, `HNT`, `JUP`

### Phase 4 - Ist-Bestand-Snapshots

Script: `scripts/collect_platform_balance_snapshots.py`

Aufgaben:

- Binance API aktuelle Balances.
- Pionex API aktuelle Balances.
- Bitget API aktuelle Balances, soweit API-Zeitraum/Scope erlaubt.
- Solana RPC/Solscan Wallet-Balances.
- Optional manuelle CSV-Snapshots.
- Ausgabe:
  - `var/platform_balance_snapshots_2026-05-09.json`
  - `docs/133_PLATFORM_BALANCE_SNAPSHOTS_2026-05-09.md`

### Phase 5 - Reconciliation

Script: `scripts/reconcile_platform_ledger_to_snapshots.py`

Aufgaben:

- Simulierten Endbestand gegen Ist-Snapshot vergleichen.
- Differenzen nach Materialitaet sortieren.
- Erkennen:
  - fehlender Transfer,
  - doppelte Referenz,
  - fehlender Opening-Bestand,
  - Plattform-interner Umbuchungskontext,
  - Dust/Rounding.
- Ausgabe:
  - `var/platform_reconciliation_2026-05-09.json`
  - `docs/134_PLATFORM_RECONCILIATION_2026-05-09.md`

### Phase 6 - Lokale KI Analyse

Script: `scripts/ai_platform_reconciliation_review.py`

Aufgaben:

- Nur Top-Probleme aus Reconciliation an lokale KI geben.
- Keine Rohdatenflut, sondern je Problem kompaktes Paket.
- KI soll Hypothesen ranken:
  - fehlende Quelle,
  - Transfergruppe wahrscheinlich,
  - Opening-Balance plausibel,
  - Referenzduplikat wahrscheinlich,
  - manuell zu entscheiden.
- Ausgabe:
  - `var/ai_platform_reconciliation_review_2026-05-09.json`
  - `docs/135_AI_PLATFORM_RECONCILIATION_REVIEW_2026-05-09.md`

## Entscheidungsmatrix

Automatisch erlaubt:

- Referenzduplikate ausschliessen, wenn Primary-Paarung exakt ist.
- Dust unter definierter Toleranz als nicht blockierend markieren.
- Transfergruppen mit gleicher TXID bilden.
- Reports und Review-Kandidaten erzeugen.

Nur mit expliziter fachlicher Entscheidung:

- Opening-Balance steuerwirksam machen.
- Pionex-USDT-Startbestand als Ersatzrekonstruktion akzeptieren.
- Bitget-2025 ohne Supportdaten finalisieren.
- Fehlende Bot-Trades rekonstruieren.

Nicht erlaubt:

- KI darf keine Buchung direkt steuerwirksam erzeugen.
- Kein Loeschen von RAW-Daten.
- Keine pauschale Doppelimportierung alter Binance/Pionex/Blockpit-Dateien.

## Erwarteter Nutzen fuer aktuellen Blocker

Pionex-USDT:

- Sichtbare Transfers Binance -> Pionex sind gruppiert.
- Pionex-only Trading-Verbrauch wird gegen Pionex-Deposits und heutigen API-Bestand simuliert.
- Der Rest `125.5260918462 USDT` wird entweder:
  - durch ein fehlendes Transferpaar erklaert,
  - als Plattform-Opening-Rest quantifiziert,
  - oder als fachliche Ersatzrekonstruktion dokumentiert.

HNT-Staking/Legacy:

- Legacy-HNT -> Binance-HNT -> Binance-USDT -> Pionex-USDT wird als Transfer-/Trade-Kette sichtbar.
- Direkter HNT-Deposit zu Pionex bleibt nur dann Thema, wenn eine Quelle ausserhalb des aktuellen Pionex Deposit/Withdraw-CSV auftaucht.

Bitget:

- vorhandene 2024/2025 API-/Blockpit-/Solana-Events werden platform-lokal simuliert.
- Support-Export kann spaeter als weitere Primary-Quelle gegen dieselben Transfergruppen verglichen werden.

## Naechster konkreter Arbeitsschritt

Mit Phase 1 beginnen:

1. `scripts/build_platform_ledger.py` implementieren.
2. Export auf aktuellen Effektivdaten ausfuehren.
3. Report `docs/130_PLATFORM_LEDGER_EXPORT_2026-05-09.md` erzeugen.
4. Danach Phase 2 Transfergruppen.
