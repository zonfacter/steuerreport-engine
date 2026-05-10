# Pionex USDT Opening-Balance Review - 2026-05-08

## Summary

- Basis: effektive Events nach Review-Actions und Tax-Overrides, Stand nach Binance-Simple-Earn-Import.
- Scope: Pionex-only `USDT`, Jahre `2021` bis `2024`.
- Events: `906`
- Pionex-only Endbestand: `0.89137980652611250000 USDT`
- Tiefster Pionex-only Bestand: `-1643.40556756620000000000 USDT`
- Erforderlicher rechnerischer Startbestand, damit Pionex-only nie negativ wird: `1643.40556756620000000000 USDT`

## Erster Pionex-only Bruch

- Zeit: `2021-12-28T00:49:12+00:00`
- Event: `dbf50e86f138a6ee50238468278e3f19517edfa373ab9b1e025a92c4e21139dd`
- Typ: `pionex` / `trade` / `out`
- Menge: `16.02000000000000000000 USDT`
- Bestand vorher: `2.48956657000000000000 USDT`
- Bestand nachher: `-13.53043343000000000000 USDT`
- Tx: `s_3:13:out:USDT`

## Schlimmster Pionex-only Bruch

- Zeit: `2022-01-19T23:28:01+00:00`
- Event: `7ba599acc2c76180d3f572985a30b19b379e5391fedb433874d042464142e12c`
- Typ: `pionex` / `fee` / `out`
- Menge: `0.17434645 USDT`
- Bestand vorher: `-1643.23122111620000000000 USDT`
- Bestand nachher: `-1643.40556756620000000000 USDT`
- Tx: `s_10:69:fee:USDT`

## Jahres-Netto Pionex-only USDT

- `2021`: `124.93443059000000000000 USDT`
- `2022`: `-110.69275736536000000000 USDT`
- `2023`: `-14.24153416170000000000 USDT`
- `2024`: `0.89124074358611250000 USDT`

## Interpretation

Der Pionex-only Strom ist am Ende nahezu geschlossen, laeuft aber im Zeitraum vor den spaeteren bekannten Einzahlungen deutlich negativ. Das ist typisch fuer fehlendes Start-/Botkapital oder eine fehlende Konto-/Bot-Statement-Zeile vor dem ersten Trade, nicht fuer einen einzelnen falschen Trade.

Der Wert `1643.40556756620000000000 USDT` ist daher ein Review-Kandidat fuer einen dokumentierten Opening-Balance-/Bot-Capital-Adjustment, falls Pionex keine aeltere Primaerquelle mehr liefern kann.

## Virtuelle Wirkung bei Annahme des Kandidaten

Diese Simulation nutzt denselben Movement-Builder wie `scripts/chronological_balance_break_audit.py`, bucht aber nichts dauerhaft:

- Virtueller Kandidat: `+1643.40556756620000000000 USDT` am `2021-12-28T00:49:11+00:00`
- Globaler USDT-Endbestand danach nach Binance-Jan-/Feb-2022-Transaction-History-Import und Solscan-Bitget-Counterflow-Import: `2333.23768980016511250000 USDT`
- Erster globaler Negativbestand danach: keiner
- Schlimmster globaler USDT-Stand danach:
  - Zeit: `2021-02-09T20:58:27+00:00`
  - Quelle: `binance` / `trade` / `out`
  - Delta: `-123.999744 USDT`
  - Bestand vorher: `124.220000 USDT`
  - Bestand nachher: `0.220256 USDT`

Schlussfolgerung: Der Pionex-Opening-Kandidat behebt den Pionex-only Startbruch vollstaendig. Die vorherigen globalen Brueche am `2022-01-19` und `2022-03-01` sind durch eng begrenzte Binance-Transaction-History-Primaerimporte geschlossen. Der spaetere Solana/Jupiter-Bruch am `2024-12-04` ist durch einen bestaetigten Solscan-Bitget-Counterflow vom `2024-12-01` geschlossen. Mit virtuellem Pionex-Kandidaten gibt es aktuell keinen globalen USDT-Negativbestand. Details stehen in `docs/66_USDT_GLOBAL_RESIDUAL_AFTER_PIONEX_CANDIDATE_2026-05-08.md`, `docs/67_BINANCE_TRANSACTION_HISTORY_JAN2022_GAP_IMPORT_2026-05-08.md`, `docs/69_BINANCE_TRANSACTION_HISTORY_FEB2022_GAP_IMPORT_2026-05-08.md` und `docs/71_SOLSCAN_BITGET_COUNTERFLOW_DEC2024_IMPORT_2026-05-08.md`.

## Nicht automatisch buchen

- Kein RAW-Event wurde geloescht oder geaendert.
- Es wurde kein Opening-Balance-Adjustment gebucht.
- Der Kandidat ist maschinenlesbar unter `GET /api/v1/review/balance-adjustment-candidates` gespeichert:
  - `candidate_id`: `pionex-usdt-opening-balance-2021-12-28`
  - `tax_effective`: `false`
  - `status`: `needs_evidence`
- Vor einer Buchung muss fachlich entschieden werden, ob der fehlende Betrag durch Pionex Account Statement, Bot-Startkapital, Support-Auskunft oder eine manuell dokumentierte Ersatzrekonstruktion belegt wird.

## Naechster Schritt

1. Pionex Account-/Bot-Statement fuer `2021-12-25` bis `2022-02-25` suchen/anfordern.
2. Wenn nicht verfuegbar: Adjustment-Review mit Betrag `1643.40556756620000000000 USDT` vorbereiten, aber klar als Ersatzrekonstruktion dokumentieren.
3. Danach die verbleibenden kleinen Dust-/Restassets pruefen: `VTHO`, `BUSD`.
