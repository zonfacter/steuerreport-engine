# Pionex Full Export Audit 2026-05-08

Quelle: `/workspace/steuerreport/usertransfer/pionex`

## Dateien
- `deposit-withdraw.csv`: `6` Zeilen, Zeitraum `2021-12-25 16:23:04` bis `2024-11-22 16:14:05`
- `dust-collector.csv`: `2` Zeilen, Zeitraum `2024-03-12 04:44:43` bis `2024-03-12 04:44:43`
- `for-cointracker.csv`: `605` Zeilen, Zeitraum `01/01/2022 00:13:19` bis `12/31/2021 23:58:07`
- `for-cointracking.csv`: `605` Zeilen, Zeitraum `01/01/2022 00:13:19` bis `12/31/2021 23:58:07`
- `others.csv`: `0` Zeilen, Zeitraum `` bis ``
- `position_futures.csv`: `0` Zeilen, Zeitraum `` bis ``
- `raw-trading-details.csv`: `11864` Zeilen, Zeitraum `2021-12-25 16:25:25` bis `2024-11-22 16:13:13`
- `staking.csv`: `0` Zeilen, Zeitraum `` bis ``
- `structured-products.csv`: `0` Zeilen, Zeitraum `` bis ``
- `trading.csv`: `597` Zeilen, Zeitraum `2021-12-25 16:25:25` bis `2024-11-22 16:13:13`

## Import-/Abdeckungsbefund
- Effektive Pionex-Events nach Overrides: `1801`
- Eventtypen: `{'deposit': 4, 'dust_trade': 4, 'withdrawal': 2, 'trade': 1194, 'fee': 597}`
- Quellen: `{'pionex': 1801}`
- `raw-trading-details.csv` vs `trading.csv`: `0` Summen-Abweichungen ueber `16` tax_id-Gruppen.

## Effektive Deposits/Withdrawals
- `2021-12-25T16:23:04+00:00` `deposit` `in` `200.00000000 USDT` tx=`b742f811bf6372301484d585166ebb0f334996185285c8fc91ced3830c724182`
- `2022-01-19T12:54:09+00:00` `deposit` `in` `1245.38419000 USDT` tx=`b930ad780ec33e9ece0a5945404674d89e0b9fa165ed9d02602fab57d6a217aa`
- `2022-02-23T05:41:40+00:00` `deposit` `in` `696.82747400 USDT` tx=`a08ff362825ec9a4ce35a3f4803cf1dba32cf1deaae4fc58281001b6a0692566`
- `2022-02-25T21:35:15+00:00` `deposit` `in` `983.69132300 USDT` tx=`9542656804be81094930fd1ddb83710f82c54fda18b2691c1ffd57b95d89a132`
- `2023-06-09T16:19:26+00:00` `withdrawal` `out` `20530.34420000 MXC` tx=`0x049701b4cddcd5bd5a2f5d3339922d8f4d771543bf51d608738da5f117db2014`
- `2024-11-22T16:14:05+00:00` `withdrawal` `out` `0.08995500 SOL` tx=`4yH7iwag7grZqxEpkWmNFYqKnRypzuPPkMXmwmuWTyUqXGTzwRdrXagsP9BitUftzanhC38FSWV5G8RZijG4JGy9`

## USDT-Bilanz Pionex intern
- Erster negativer Pionex-USDT-Stand: `{'balance': '-13.53043343000000000000', 'timestamp_utc': '2021-12-28T00:49:12+00:00', 'event_type': 'trade', 'side': 'out', 'quantity': '16.02000000000000000000', 'tx_id': 's_3:13:out:USDT'}`
- Schlimmster Pionex-USDT-Stand: `{'balance': '-1643.40556756620000000000', 'timestamp_utc': '2022-01-19T23:28:01+00:00', 'event_type': 'fee', 'side': 'out', 'quantity': '0.17434645', 'tx_id': 's_10:69:fee:USDT'}`
- Finaler Pionex-USDT-Stand im Modell: `0.89137980652611250000`

## Bewertung
- Der Export enthaelt faktisch Daten ab `2021-12-25`, nicht ab 2019. Leere Dateien fuer Futures/Staking/Structured/Others enthalten keine Startbestaende.
- `raw-trading-details.csv` liefert Fill-Details, aber keine zusaetzlichen Summen gegenueber `trading.csv`; ein Import wuerde die bestehenden Trades duplizieren.
- `for-cointracking.csv` und `for-cointracker.csv` sind abgeleitete Exportformate derselben Pionex-Daten und sollten nicht zusaetzlich importiert werden.
- Die echte offene Pionex-Frage bleibt ein nicht im Export enthaltener Start-/Bot-Bestand oder fehlende externe Zufuehrung vor dem ersten negativen USDT-Punkt.
