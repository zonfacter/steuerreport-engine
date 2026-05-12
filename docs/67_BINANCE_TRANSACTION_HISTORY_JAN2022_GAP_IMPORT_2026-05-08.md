# Binance Transaction History Jan 2022 Gap Import - 2026-05-08

## Zweck

Eng begrenzter Primaerimport aus dem Binance `Transaction History` Export, um die USDT-Luecke vor dem Pionex-Transfer am `2022-01-19` zu pruefen.

## Import

- Quelle: `/workspace/steuerreport/usertransfer/Binance/export 2021/Binance-Transaction-History-202605061835(UTC+2)_344d77e2.xlsx`
- Source Name: `binance_transaction_history_jan2022_gap_2026-05-08`
- Normalisierte Ledger-Zeilen: `90`
- Inserted Events: `90`
- Duplicate Events: `0`
- Ausgeschlossen: Withdrawals/Deposits, damit Binance-API-Transfers nicht dupliziert werden.

## Netto nach Asset

- `HNT`: `-47.919860000000`
- `USDT`: `1246.375247000000`

## Hinweis

Die Ledger-Zeilen kommen aus Binance Transaction History und enthalten keine Order-IDs. Deshalb wurden deterministische `tx_id` Werte mit Zeit, Zeilenindex, Operation und Coin erzeugt. Der Import ist absichtlich auf Januar 2022 bis direkt vor die Pionex-Auszahlung begrenzt.
