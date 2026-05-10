# Binance 2021 Account Statement Income Import - 2026-05-09

## Zweck

Dedizierter Importpfad fuer die geprueften Binance-Account-Statement-Income-Zeilen aus der Legacy-Pivot-Datei.

## Lauf

- Modus: `preview`
- Quelle: `/workspace/steuerreport/usertransfer/legacy_daten/Steuer-2021/Binance-export/BINANCE - TRADING - Export - PIVOT.xlsx`
- Sheet: `part-00000-3d734e3b-9531-4c31-9`
- Asset Filter: `{'assets': [], 'exclude_assets': ['NFT']}`
- Zeilen: `311`
- Unique Events: `311`
- Existing Duplikate: `311`
- Neue Kandidaten: `0`
- Summary: `{'counts_by_asset': {'ADA': 276, 'DOGE': 28, 'USDT': 7}, 'totals_by_asset': {'ADA': '0.06117724', 'DOGE': '0.85150592', 'USDT': '0.00080654'}, 'counts_by_event_type': {'interest': 311}, 'first_timestamp_utc': '2021-02-14T01:36:41+00:00', 'last_timestamp_utc': '2022-01-01T03:11:05+00:00'}`

## Bewertung

- This importer only covers reviewed income-like rows: Savings Interest and Distribution.
- Savings purchase and principal redemption rows are intentionally excluded as principal/product movements.
- Prepared 311 rows; 0 unique rows do not currently exist by import fingerprint.
- Rows have synthetic tx_id values because the Binance account statement sheet has no transaction ids.
- Preview only: no RAW events were written.
- 311 rows already matched existing RAW event fingerprints.

## Hinweis

Diese Zeilen sind klein, aber potentiell steuerlich relevant. Vor Execute sollten Preise/EUR-Bewertung und NFT-Symbolbehandlung geprueft werden.
