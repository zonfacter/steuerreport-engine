# USDT 2022 Restblock nach HNT-Schliessung

Stand: 2026-05-12

## Ergebnis

- Verbleibende HNT/USDT-Zero-Cost-Zeilen >= 50 EUR: `3`
- Asset: `USDT 2022`
- Menge: `1569.8280684762 USDT`
- Erloes: `1383.876662295203014 EUR`
- HNT ist nach dem Roundtrip-Match nicht mehr im >=50-EUR-Restblock enthalten.
- Es wurde kein automatischer Preis-, FX- oder Cost-Basis-Fix abgeleitet.

## Aktuelle Jobs

| Jahr | Job | Tax Lines | Derivative Lines | Aktualisiert |
| --- | --- | --- | --- | --- |
| 2021 | `e26811e1-becc-477f-a83c-fdf60cea327b` | 5454 | 43 | 2026-05-12T19:05:43.826732+00:00 |
| 2022 | `d1c40860-d286-4ff7-a7e7-1a173f99ad4e` | 11765 | 630 | 2026-05-11T21:29:04.737184+00:00 |

## Offene Zeilen

| Line | Asset | Menge | Zeit | Erloes EUR | Quelle |
| --- | --- | --- | --- | --- | --- |
| 412 | USDT | 75.10462220620000000000 | 2022-01-05T15:36:46+00:00 | 66.3526805805115140000000000 | fe030531d67b... |
| 442 | USDT | 168.76468350000000000000 | 2022-01-19T12:45:42+00:00 | 148.7576302710750000000000000 | a20292c0e922... |
| 514 | USDT | 1325.95876277000000000000 | 2022-01-19T12:56:19+00:00 | 1168.766351443616500000000000 | b5422e7c322b... |

## Raw-Event-Kontext

| Line/Event | Quelle | Typ | Side | Menge | Tx/Raw | Roh-Kontext |
| --- | --- | --- | --- | --- | --- | --- |
| fe030531d67b... | binance | trade | out | 186.270000 | binance-txhist-jan2022:20220105T173646:2016:Transaction Spend:USDT | Transaction Spend |
| a20292c0e922... | pionex | trade | out | 479.99307717000000000000 | s_10:67:out:USDT | MXC_USDT |
| b5422e7c322b... | pionex | trade | out | 2572.15382077000000000000 | s_11:68:out:USDT | MXC_USDT |

## Binance 2022-01-05

- USDT-In aus sichtbaren Binance-Bewegungen: `1916.535 USDT`
- USDT-Out inkl. Fees: `3788.554236 USDT`
- Fees: `1.916536 USDT`
- Tagesnetto: `-1872.019236 USDT`
- Der 2022-01-05-Rest ist damit kein reiner Sortier- oder Dezimalfehler.

## Lokale Pionex-Dateien

| Ordner | Datei | Zeilen | Fruehe USDT-Zeilen |
| --- | --- | --- | --- |
| usertransfer/pionex | deposit-withdraw.csv | 6 | 2 |
| usertransfer/pionex | trading.csv | 597 | 107 |
| usertransfer/pionex | raw-trading-details.csv | 11864 | 2935 |
| usertransfer/pionex | for-cointracker.csv | 605 | 166 |
| usertransfer/pionex | for-cointracking.csv | 605 | 166 |
| usertransfer/pionex | others.csv | 0 | 0 |
| usertransfer/pionex | staking.csv | 0 | 0 |
| usertransfer/pionex | structured-products.csv | 0 | 0 |
| usertransfer/pionex | position_futures.csv | 0 | 0 |
| usertransfer/pionex | dust-collector.csv | 2 | 0 |
| usertransfer/pionex_txn_2021-12-31_2022-12-30_gen_2026-05-05 | deposit-withdraw.csv | 3 | 1 |
| usertransfer/pionex_txn_2021-12-31_2022-12-30_gen_2026-05-05 | trading.csv | 562 | 83 |
| usertransfer/pionex_txn_2021-12-31_2022-12-30_gen_2026-05-05 | raw-trading-details.csv | 11330 | 2415 |
| usertransfer/pionex_txn_2021-12-31_2022-12-30_gen_2026-05-05 | for-cointracker.csv | 565 | 132 |
| usertransfer/pionex_txn_2021-12-31_2022-12-30_gen_2026-05-05 | for-cointracking.csv | 565 | 132 |
| usertransfer/pionex_txn_2021-12-31_2022-12-30_gen_2026-05-05 | others.csv | 0 | 0 |
| usertransfer/pionex_txn_2021-12-31_2022-12-30_gen_2026-05-05 | staking.csv | 0 | 0 |
| usertransfer/pionex_txn_2021-12-31_2022-12-30_gen_2026-05-05 | structured-products.csv | 0 | 0 |
| usertransfer/pionex_txn_2021-12-31_2022-12-30_gen_2026-05-05 | position_futures.csv | 0 | 0 |
| usertransfer/pionex_txn_2021-12-31_2022-12-30_gen_2026-05-05 | dust-collector.csv | 0 | 0 |

## Importierte Pionex-Quellen

| Quelle | Rows |
| --- | --- |
| pionex:pionex_txn_2021-12-31_2022-12-30_gen_2026-05-05:deposit-withdraw.csv | 3 |
| pionex:pionex_txn_2021-12-31_2022-12-30_gen_2026-05-05:trading.csv | 1686 |
| pionex:pionex_txn_2022-12-31_2023-12-30_gen_2026-05-05:deposit-withdraw.csv | 1 |
| pionex:pionex_txn_2022-12-31_2023-12-30_gen_2026-05-05:trading.csv | 21 |
| pionex:pionex_txn_2023-12-31_2024-12-30_gen_2026-05-05:deposit-withdraw.csv | 1 |
| pionex:pionex_txn_2023-12-31_2024-12-30_gen_2026-05-05:dust-collector.csv | 4 |
| pionex:pionex_txn_2023-12-31_2024-12-30_gen_2026-05-05:trading.csv | 12 |
| pionex:unified_2026-05-06:deposit-withdraw.csv | 1 |
| pionex:unified_2026-05-06:trading.csv | 1791 |
| pionex_inferred_missing_deposit_from_binance_2021-12-25_usdt.csv | 1 |

## Einordnung

- Line `412` ist Binance-USDT-Verbrauch am `2022-01-05`; am selben Tag sind HNT/USDT-Verkaeufe sichtbar, aber die spaeteren USDT-Spends uebersteigen den belegten Tagesbestand.
- Lines `442` und `514` sind Pionex-`MXC_USDT`-BUY-Kontext; das erklaert die USDT-Verwendung, aber nicht die vorherige USDT-Herkunft.
- `raw-trading-details.csv` liefert mehr Fill-Details, aber keine separate Opening-Balance oder Strategy-/Bot-Kapitalbuchung.
- Nebenlisten `others`, `staking`, `structured-products`, `position_futures` sind fuer den fruehen USDT-Block leer.
- Naechster sicherer Schritt bleibt ein Primaerbeleg: Pionex Opening Balance, Bot/Grid-/Strategy-Statement oder eine explizite Review-Entscheidung.
