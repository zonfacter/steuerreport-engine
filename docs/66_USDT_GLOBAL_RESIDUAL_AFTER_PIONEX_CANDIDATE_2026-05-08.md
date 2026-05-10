# USDT Global Residual After Pionex Candidate - 2026-05-08

## Ziel

Dieser Report trennt zwei Sachverhalte:

- Pionex-only USDT ist mit dem Review-Kandidaten `pionex-usdt-opening-balance-2021-12-28` rechnerisch geschlossen.
- Global bleibt danach eine USDT-Unterdeckung im Gesamtbestand. Diese darf nicht automatisch als zweiter Pionex-Opening-Balance gebucht werden.

## Ausgangspunkt

- Virtueller, nicht steuerwirksamer Kandidat: `+1643.40556756620000000000 USDT`
- Zeitpunkt: `2021-12-28T00:49:11+00:00`
- Effekt Pionex-only:
  - Endbestand ohne Kandidat: `0.89137980652611250000 USDT`
  - Tiefster Bestand ohne Kandidat: `-1643.40556756620000000000 USDT`
  - Tiefster Bestand mit Kandidat: `0 USDT`
  - Ergebnis: Pionex-only ist durch genau diesen Kandidaten nicht mehr negativ.

## Urspruenglicher globaler Bruch vor Binance-Jan-2022-Import

- Zeit: `2022-01-19T12:56:19+00:00`
- Event-ID: `b5422e7c322b53d701869335a500c9b7e48334f50b6e8410978e247e608e0399`
- Quelle: `pionex`
- Event-Typ: `trade`
- Tx: `s_11:68:out:USDT`
- Markt: `MXC_USDT`
- Side: `BUY`
- USDT-Abfluss: `2572.15382077000000000000 USDT`
- Globaler USDT-Bestand vorher: `1399.27305295000000000000 USDT`
- Globaler USDT-Bestand nachher: `-1172.88076782000000000000 USDT`

Gegenbuchungen aus derselben Pionex-Rohzeile:

- Event-ID `b16394b3e465c1c9899fca091cec61633029e2e9b7cce152fea43c7a3ed7d30e`
- Tx `s_11:68:in:MXC`
- Eingang `21823.27000000000000000000 MXC`
- Event-ID `f9f5415f90c24b5f18da573432f4ed5e98c08dc45f6a0bbf08153b1570ed4241`
- Tx `s_11:68:fee:MXC`
- Fee `10.91163500 MXC`

Raw Row:

```json
{
  "amount": "2572.15382077000000000000",
  "date(UTC+0)": "2022-01-19 12:56:19",
  "executed_qty": "21823.27000000000000000000",
  "fee": "10.91163500",
  "fee_coin": "MXC",
  "market_type": "Spot",
  "price": "0.11786290",
  "side": "BUY",
  "symbol": "MXC_USDT",
  "tax_id": "s_11"
}
```

## Kontext direkt davor

- `2022-01-19T12:45:42+00:00`: Pionex Trade out `-479.99307717000000000000 USDT`, global danach `1399.27305295000000000000 USDT`
- `2022-01-19T12:50:48+00:00`: Binance Withdrawal `-1245.38419 USDT`, Tx `b930ad780ec33e9ece0a5945404674d89e0b9fa165ed9d02602fab57d6a217aa`
- `2022-01-19T12:54:09+00:00`: Pionex Deposit `+1245.38419000 USDT`, gleiche Tx `b930ad780ec33e9ece0a5945404674d89e0b9fa165ed9d02602fab57d6a217aa`
- Globaler Effekt dieses Transfers: `0 USDT`
- Bestand vor `s_11:68`: weiterhin `1399.27305295000000000000 USDT`

## Globale USDT-Quellen bis direkt vor dem Bruch

Mit virtuellem Pionex-Kandidaten ergibt sich vor `2022-01-19T12:56:19+00:00`:

| Quelle | Netto USDT |
|---|---:|
| `review_candidate` | `1643.40556756620000000000` |
| `pionex` | `928.92259965380000000000` |
| `binance` | `272.34353073` |
| `binance_api` | `-1445.39864500` |
| Summe vor Bruch | `1399.27305295000000000000` |

Wichtige Detailpositionen:

| Quelle / Typ / Seite | Netto USDT |
|---|---:|
| `binance` / `trade` / `out` | `-46892.72026327` |
| `binance` / `trade` / `in` | `45726.83467400` |
| `pionex` / `trade` / `out` | `-2220.09374159960000000000` |
| `pionex` / `trade` / `in` | `1704.48439361340000000000` |
| `review_candidate` / `opening_balance_candidate` / `candidate_in` | `1643.40556756620000000000` |
| `pionex` / `deposit` / `in` | `1445.38419000` |
| `binance_api` / `withdrawal` / `out` | `-1445.38419` |
| `binance` / `fiat_crypto_purchase` / `in` | `1438.229120` |

## Bewertung

Der `s_11:68`-Bruch ist kein Dezimaltrennzeichen- oder Vorzeichenfehler. Die Pionex-Rohzeile beschreibt einen Spot-Kauf von `MXC` gegen `USDT`; der USDT-Abfluss ist durch `amount`, `price` und `executed_qty` konsistent.

Vor dem Binance-Jan-2022-Import bedeutete der Bruch: Im globalen Modell waren vor diesem Trade `1172.88076782000000000000 USDT` zu wenig verfuegbar. Moegliche Ursachen waren:

- damals hypothetisch: weiterer fehlender Pionex-Account-/Bot-Startbestand vor `2022-01-19T12:56:19Z`
- fehlender externer Transfer oder nicht importierter CEX-/Wallet-Ausschnitt vor dem Trade
- fehlende Statement-Zeile innerhalb Pionex, die nicht im CSV-Export enthalten ist
- zeitliche/semantische Modellgrenze, falls Pionex Bot-Kapital intern anders bereitgestellt wurde als die Trade-Historie zeigt

## Nach Binance-Jan-2022-Transaction-History-Import

Der Import `binance_transaction_history_jan2022_gap_2026-05-08` hat `90` Binance-Ledger-Zeilen aus dem Januar 2022 eingefuegt:

- Report: `docs/67_BINANCE_TRANSACTION_HISTORY_JAN2022_GAP_IMPORT_2026-05-08.md`
- Netto: `+1246.375247000000 USDT`
- Netto: `-47.919860000000 HNT`
- Withdrawals/Deposits wurden absichtlich nicht importiert, damit Binance-API-Transfers nicht dupliziert werden.

Danach ist `s_11:68` nicht mehr negativ:

- Bestand vor `s_11:68`: `2645.64829995000000000000 USDT`
- Pionex Trade out: `-2572.15382077000000000000 USDT`
- Bestand nach `s_11:68`: `73.49447918000000000000 USDT`

Damit ist der Januar-2022-Bruch geschlossen. Danach lag mit virtuellem Pionex-Opening-Kandidaten der naechste globale USDT-Bruch zunaechst bei:

- Zeit: `2022-03-01T05:35:52+00:00`
- Quelle: `pionex` / `trade` / `out`
- Tx: `s_14:207:out:USDT`
- Delta: `-1758.12543600000000000000 USDT`
- Bestand vorher: `1688.47843648000000000000 USDT`
- Bestand nachher: `-69.64699952000000000000 USDT`

## Nach Binance-Feb-2022-Transaction-History-Import

Der Import `binance_transaction_history_feb2022_gap_2026-05-08` hat `9` weitere Binance-Ledger-Zeilen eingefuegt:

- Report: `docs/69_BINANCE_TRANSACTION_HISTORY_FEB2022_GAP_IMPORT_2026-05-08.md`
- Netto: `+1682.518797000000 USDT`
- Netto: `-72.870000000000 HNT`
- Withdrawals/Deposits und Earn-Bewegungen wurden absichtlich nicht importiert.

Danach ist auch `s_14:207` nicht mehr negativ:

- Bestand vor `s_14:207`: `3370.99723348000000000000 USDT`
- Pionex Trade out: `-1758.12543600000000000000 USDT`
- Bestand nach `s_14:207`: `1612.87179748000000000000 USDT`

Mit virtuellem Pionex-Opening-Kandidaten lag der erste verbleibende globale USDT-Bruch nach diesem Stand zunaechst bei:

- Zeit: `2024-12-04T18:30:59+00:00`
- Quelle: `solana_rpc` / `token_transfer` / `out`
- Tx: `XWx5SFmBAFGyHBYFRq8qrfyoznbNsv5T4NJcnXrFN28s94teAGyv7k2t7bCJ4T8LBbpFPM5vqrT3CfvrMnXMTfW`
- Delta: `-2764.708247 USDT`
- Bestand vorher: `2498.60048034572611250000 USDT`
- Bestand nachher: `-266.10776665427388750000 USDT`
- Globaler USDT-Endbestand mit virtuellem Kandidaten: `345.22942980016511250000 USDT`

## Nach Solscan-Bitget-Counterflow-Import

Der Import `solscan_bitget_counterflow_dec2024_2026-05-08` hat den fehlenden On-Chain-Gegenfluss fuer die Bitget-Auszahlung vor dem Jupiter-Swap als Primaerquelle eingefuegt:

- Report: `docs/71_SOLSCAN_BITGET_COUNTERFLOW_DEC2024_IMPORT_2026-05-08.md`
- Signatur: `mxDAzS4vybHXsuUscyeXTrAQwsjKz3pbs9hHpZp6Ld68iMjHetSWahTCVf1MG4Uakbme7ZsWGMcJPEUTkXPhNus`
- Zeit: `2024-12-01T13:32:32+00:00`
- Event: `token_transfer` / `in`
- Menge: `1988.00826 USDT`
- Quelle: `solscan_account_transfers`; diese Zeile war schon als Transfer-Indiz vorhanden, aber vorher nicht als effektives RAW-Event aktiv.

Damit ist auch der Solana/Jupiter-Swap `XWx5SFm...XMTfW` nicht mehr negativ:

- Bestand vor `XWx5...`: `4486.60874034572611250000 USDT`
- Swap out: `-2764.708247 USDT`
- Bestand nach `XWx5...`: `1721.90049334572611250000 USDT`

Mit virtuellem Pionex-Opening-Kandidaten gibt es aktuell keinen globalen USDT-Negativbestand mehr:

- Globaler USDT-Endbestand: `2333.23768980016511250000 USDT`
- Erster globaler Negativbestand: keiner
- Schlimmster globaler USDT-Stand: `0.220256 USDT` am `2021-02-09T20:58:27+00:00`

## Keine automatische Buchung

Es wurde kein zweiter Adjustment-Kandidat angelegt. Der bestehende Pionex-Kandidat bleibt `tax_effective=false`. Die Januar-/Februar-2022-Brueche wurden durch Primaerdaten aus Binance geschlossen; der Dezember-2024-Bruch wurde durch einen Primaer-On-Chain-Gegenfluss aus Solscan geschlossen.

## Naechste Pruefung

1. Pionex Opening-/Bot-Startbestand weiter belegen, bevor der bestehende Kandidat steuerwirksam gemacht wird.
2. Verbleibende kleine Dust-/Restassets aus dem neuesten Audit pruefen: `VTHO`, `BUSD`.
3. Weitere Binance-Transaction-History-Zeitfenster nur bei konkretem Fehlersignal importieren, damit vorhandene Trade-Exports nicht dupliziert werden.
