# Binance Transaction History Feb 2022 Gap Import - 2026-05-08

## Zweck

Eng begrenzter Primaerimport aus dem Binance `Transaction History` Export, um die USDT-Luecke vor dem Pionex-Bruch am `2022-03-01` zu pruefen.

## Import

- Quelle: `/workspace/steuerreport/usertransfer/Binance/export 2021/Binance-Transaction-History-202605061835(UTC+2)_344d77e2.xlsx`
- Source Name: `binance_transaction_history_feb2022_gap_2026-05-08`
- Normalisierte Ledger-Zeilen: `9`
- Inserted Events: `9`
- Duplicate Events: `0`
- Ausgeschlossen: Withdrawals/Deposits und Earn-Bewegungen, damit Transfers und interne Earn-Umbuchungen nicht dupliziert werden.

## Netto nach Asset

- `HNT`: `-72.870000000000`
- `USDT`: `1682.518797000000`

## Hinweis

Der Import enthaelt nur Binance-Transaction-Ledger-Zeilen mit `Transaction Revenue`, `Transaction Sold` und `Transaction Fee` im engen Zeitfenster nach dem Januar-Gap bis Ende `2022-02-25`.
