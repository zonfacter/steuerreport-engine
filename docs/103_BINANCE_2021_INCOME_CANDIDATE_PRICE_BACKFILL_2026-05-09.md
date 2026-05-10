# Binance 2021 Income Candidate Price Backfill - 2026-05-09

## Zweck

Gezielter Yahoo-Preisbackfill fuer bewertbare Binance-2021-Ertragskandidaten vor Importentscheidung.

- Dry Run: `False`
- Assets: `['ADA', 'DOGE']`

## Ergebnis

- `{'symbol': 'ADA', 'ticker': 'ADA-USD', 'status': 'ok', 'dates': 275, 'cached': 275, 'missing': [], 'first_date': '2021-03-30', 'last_date': '2022-01-01'}`
- `{'symbol': 'DOGE', 'ticker': 'DOGE-USD', 'status': 'ok', 'dates': 28, 'cached': 28, 'missing': [], 'first_date': '2021-03-30', 'last_date': '2021-04-28'}`

## Bewertung

- This backfill is restricted to configured Yahoo tickers needed by the reviewed Binance 2021 income candidates.
- NFT/APENFT is intentionally excluded here because the Binance symbol needs explicit mapping before automated price use.
